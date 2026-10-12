"""Экспорт тем Arizona RP Forum через Arizona-Forum-API-Async.

Стиль запуска — как в examples библиотеки: настройте значения ниже и запустите
python export_forum.py. Никаких параллельных запросов здесь нет.
"""

import asyncio
import csv
import getpass
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import arizona_forum_async as arz_api


# =========================== НАСТРОЙКИ ======================================

# Авторизация. Вместо "your" можно вставить свои значения или ввести их
# при запуске. Также поддерживаются ARZ_XF_USER и ARZ_XF_TFA_TRUST из окружения.
COOKIES = {
    "xf_user": os.getenv("ARZ_XF_USER", "your"),
    "xf_tfa_trust": os.getenv("ARZ_XF_TFA_TRUST", "your"),
}

# ID разделов через пробел, запятую, точку с запятой или перенос строки.
# Пустая строка = запросить ID при запуске. Пример: "539, 540 541".
CATEGORY_IDS = ""

# Куда сохранять: относительный путь отсчитывается от этого .py файла.
# Можно указать абсолютный, например r"D:\\Arizona\\Backup".
OUTPUT_DIR = "exports"

# Форматы отдельных файлов: "txt", "md", "json". Можно сразу несколько.
OUTPUT_FORMATS = ("txt",)                 # Пример: ("txt", "md", "json")

# Источник содержимого: "bbcode", "html", "text". Можно несколько.
# BBCode извлекается через метод библиотеки и требует дополнительных запросов.
CONTENT_TYPES = ("bbcode",)               # Пример: ("bbcode", "html", "text")

# Структура папок: "category" = по отдельной папке на каждый раздел;
# "flat" = все файлы тем в одной папке (ID темы в имени обязателен).
FOLDER_MODE = "category"
CATEGORY_FOLDER_TEMPLATE = "category_{category_id}"  # также {category_title}
THREADS_SUBFOLDER = ""                   # Например: "topics"; пусто = без подпапки

# Имя файла (без расширения). Доступны:
# {thread_id}, {title}, {author}, {author_id}, {category_id},
# {category_title}, {prefix}, {date}. Недопустимые символы заменяются.
# Если {thread_id} отсутствует в шаблоне, он добавляется автоматически.
FILE_NAME_TEMPLATE = "{thread_id}_{title}"
MAX_FILE_NAME_LENGTH = 110               # С учётом кириллицы/UTF-8
ENCODING = "utf-8-sig"                   # "utf-8" или "utf-8-sig" для Блокнота

# Какие сообщения сохранять.
INCLUDE_REPLIES = False                   # True = первое сообщение + ВСЕ ответы
INCLUDE_SUBCATEGORIES = False            # True = рекурсивный обход подразделов

# Какие темы сохранять.
EXPORT_PINNED = True
EXPORT_UNPINNED = True
EXPORT_CLOSED = True
EXPORT_OPEN = True

# Метаданные: порядок и состав для всех форматов. Можно убрать ненужные ключи.
# Допустимы: title, thread_id, url, category, category_id, category_url,
# author, author_id, created, created_unix, prefix, pinned, closed,
# first_post_id, pages_count, last_reply, last_reply_author.
INCLUDE_METADATA = True
METADATA_FIELDS = (
    "title", "thread_id", "url", "category", "category_id", "category_url",
    "author", "author_id", "created", "prefix", "pinned", "closed",
    "first_post_id", "pages_count", "last_reply", "last_reply_author",
)

# Оформление TXT / MD.
TXT_SEPARATOR = "=" * 65
INCLUDE_POST_INFO = True                 # Автор, дата и ссылка для каждого поста
DATE_FORMAT = "%d.%m.%Y %H:%M:%S"
DATE_TIMEZONE = "utc"                   # "utc" или "local"

# Дополнительные файлы рядом с темами.
SAVE_CATEGORY_INFO = True               # category_info.txt
SAVE_CSV_INDEX = True                    # index.csv
SAVE_ERRORS_LOG = True                   # errors.log (при наличии ошибок)

# Повторные запуски. False = пропуск уже существующих файлов.
OVERWRITE_EXISTING = False

# 0 = без ограничения. Удобно для пробного запуска.
MAX_THREADS_PER_CATEGORY = 0
MAX_PAGES_PER_CATEGORY = 0

# Повторы при сбоях; ограничение запросов — через очередь самой библиотеки.
RETRIES = 3
REQUEST_INTERVAL_SECONDS = 2.0
MAX_REQUESTS_PER_MINUTE = 30

# ============================================================================


FIELD_LABELS = {
    "title": "Название", "thread_id": "ID темы", "url": "Ссылка",
    "category": "Категория", "category_id": "ID категории",
    "category_url": "Ссылка на категорию", "author": "Автор",
    "author_id": "ID автора", "created": "Дата создания",
    "created_unix": "Дата создания (UNIX)", "prefix": "Префикс",
    "pinned": "Закреплена", "closed": "Закрыта",
    "first_post_id": "ID первого сообщения", "pages_count": "Страниц темы",
    "last_reply": "Последний ответ", "last_reply_author": "Последний ответил",
}

POST_LABELS = {
    "post_id": "ID сообщения", "author": "Автор", "author_id": "ID автора",
    "created": "Дата", "url": "Ссылка",
}


# ---------------------------- ПОДГОТОВКА -------------------------------------

def parse_ids(value):
    """'1 2, 3;4' -> [1, 2, 3, 4]."""
    ids = []
    for part in re.split(r"[\s,;]+", value.strip()):
        if not part:
            continue
        if not part.isdecimal() or int(part) <= 0:
            raise ValueError(f"Неверный ID категории: {part!r}")
        number = int(part)
        if number not in ids:
            ids.append(number)
    if not ids:
        raise ValueError("Не указаны ID категорий")
    return ids


def normalize_settings():
    formats = (OUTPUT_FORMATS,) if isinstance(OUTPUT_FORMATS, str) else tuple(OUTPUT_FORMATS)
    contents = (CONTENT_TYPES,) if isinstance(CONTENT_TYPES, str) else tuple(CONTENT_TYPES)
    formats = tuple(dict.fromkeys(item.lower().strip() for item in formats))
    contents = tuple(dict.fromkeys(item.lower().strip() for item in contents))
    if not formats or any(item not in ("txt", "md", "json") for item in formats):
        raise ValueError("OUTPUT_FORMATS: допускаются только txt, md и json")
    if not contents or any(item not in ("bbcode", "html", "text") for item in contents):
        raise ValueError("CONTENT_TYPES: допускаются только bbcode, html и text")
    if FOLDER_MODE not in ("category", "flat"):
        raise ValueError("FOLDER_MODE: допускаются category и flat")
    if DATE_TIMEZONE not in ("utc", "local"):
        raise ValueError("DATE_TIMEZONE: допускаются utc и local")
    if any(item not in FIELD_LABELS for item in METADATA_FIELDS):
        raise ValueError("METADATA_FIELDS содержит неизвестное поле")
    if not isinstance(MAX_FILE_NAME_LENGTH, int) or MAX_FILE_NAME_LENGTH < 24:
        raise ValueError("MAX_FILE_NAME_LENGTH должен быть не меньше 24")
    if RETRIES < 1 or MAX_PAGES_PER_CATEGORY < 0 or MAX_THREADS_PER_CATEGORY < 0:
        raise ValueError("Проверь настройки RETRIES / MAX_* (они не могут быть отрицательными)")
    if REQUEST_INTERVAL_SECONDS < 0 or MAX_REQUESTS_PER_MINUTE < 1:
        raise ValueError("Проверь ограничения очереди запросов")
    # В плоской папке ID всегда присутствует в имени: это предотвращает
    # перезапись тем из разных категорий и коллизии одинаковых названий.
    return formats, contents


def safe_name(value, limit=110):
    """Безопасная часть пути с ограничением длины В БАЙТАХ UTF-8."""
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(value or "без_названия"))
    value = re.sub(r"\s+", " ", value).strip(" .")
    result = ""
    for char in value:
        if len((result + char).encode("utf-8")) > min(limit, 190):
            break
        result += char
    result = result.rstrip(" .") or "без_названия"
    if result.upper().split(".")[0] in ("CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)], *[f"LPT{i}" for i in range(1, 10)]):
        result = "_" + result
    return result


def readable_date(timestamp):
    try:
        timestamp = int(timestamp)
        if timestamp <= 0:
            return "неизвестно"
        zone = timezone.utc if DATE_TIMEZONE == "utc" else None
        date = datetime.fromtimestamp(timestamp, tz=zone)
        return date.strftime(DATE_FORMAT) + (" UTC" if DATE_TIMEZONE == "utc" else "")
    except (ValueError, TypeError, OSError, OverflowError):
        return "неизвестно"


def prepare_paths(category, root):
    fields = {
        "category_id": str(category.id),
        "category_title": safe_name(category.title, 70),
    }
    if FOLDER_MODE == "category":
        folder = root / safe_name(CATEGORY_FOLDER_TEMPLATE.format(**fields), 150)
    else:
        folder = root
    files_folder = folder / safe_name(THREADS_SUBFOLDER) if THREADS_SUBFOLDER else folder
    files_folder.mkdir(parents=True, exist_ok=True)
    return folder, files_folder


def make_file_paths(thread, category, files_folder, formats):
    creator = getattr(thread, "creator", None)
    data = {
        "thread_id": str(thread.id),
        "title": safe_name(thread.title, 90),
        "author": safe_name(getattr(creator, "username", "") or "неизвестно", 60),
        "author_id": str(getattr(creator, "id", "") or "неизвестно"),
        "category_id": str(category.id),
        "category_title": safe_name(category.title, 60),
        "prefix": safe_name(thread.prefix or "нет", 40),
        "date": safe_name(readable_date(thread.create_date), 40),
    }
    stem = FILE_NAME_TEMPLATE.format(**data)
    # Добавляем ID всегда, если пользователь убрал {thread_id} из шаблона.
    if "{thread_id}" not in FILE_NAME_TEMPLATE:
        stem += "_" + data["thread_id"]
    # Сохраняем ID при обрезке чрезмерно длинных имён.
    if len(stem.encode("utf-8")) > MAX_FILE_NAME_LENGTH:
        stem = safe_name(stem, MAX_FILE_NAME_LENGTH - len(data["thread_id"]) - 1)
        stem += "_" + data["thread_id"]
    stem = safe_name(stem, MAX_FILE_NAME_LENGTH)
    return {ext: files_folder / f"{stem}.{ext}" for ext in formats}


def list_rows(value):
    # В текущей версии get_threads_extended() возвращает list[dict],
    # но обрабатываем и старый формат {pins: [...], unpins: [...]}.
    if isinstance(value, list):
        return [item if isinstance(item, dict) else {"thread_id": item} for item in value]
    if isinstance(value, dict):
        result = []
        for kind in ("pins", "unpins"):
            for item in value.get(kind, []):
                row = dict(item) if isinstance(item, dict) else {"thread_id": item}
                row.setdefault("is_pinned", kind == "pins")
                result.append(row)
        return result
    raise ValueError(f"Неизвестный формат ответа API: {type(value).__name__}")


def row_id(row):
    try:
        return int(row.get("thread_id") or row.get("id") or 0)
    except (TypeError, ValueError):
        return 0


def choose_row(row):
    if row.get("is_pinned") is True and not EXPORT_PINNED:
        return False
    if row.get("is_pinned") is False and not EXPORT_UNPINNED:
        return False
    if row.get("is_closed") is True and not EXPORT_CLOSED:
        return False
    if row.get("is_closed") is False and not EXPORT_OPEN:
        return False
    return True


async def retry_call(label, func, is_valid=lambda value: value is not None):
    for attempt in range(1, RETRIES + 1):
        try:
            value = await func()
            if is_valid(value):
                return value
            reason = "пустой/некорректный ответ API"
        except Exception as error:
            reason = f"{type(error).__name__}: {error}"
        print(f"  [!] {label}: {reason} (попытка {attempt}/{RETRIES})")
        if attempt < RETRIES:
            await asyncio.sleep(min(2 ** attempt, 10))
    raise RuntimeError(f"{label}: {reason}")


def write_error(folder, category_id, message):
    if not SAVE_ERRORS_LOG:
        return
    name = f"errors_{category_id}.log" if FOLDER_MODE == "flat" else "errors.log"
    with (folder / name).open("a", encoding="utf-8") as file:
        file.write(f"[{datetime.now(timezone.utc).isoformat()}] {message}\n")


def write_category_info(category, folder):
    if not SAVE_CATEGORY_INFO:
        return
    name = f"category_info_{category.id}.txt" if FOLDER_MODE == "flat" else "category_info.txt"
    (folder / name).write_text(
        f"Название: {category.title}\nID: {category.id}\nСсылка: {category.url}\n",
        encoding=ENCODING,
    )


def add_to_index(folder, category_id, metadata, paths):
    if not SAVE_CSV_INDEX:
        return
    name = f"index_{category_id}.csv" if FOLDER_MODE == "flat" else "index.csv"
    index_path = folder / name
    fieldnames = ("thread_id", "title", "author", "created", "url", "files")
    rows = []
    if index_path.exists() and index_path.stat().st_size:
        with index_path.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))

    item = {
        "thread_id": str(metadata["thread_id"]), "title": metadata["title"],
        "author": metadata["author"], "created": metadata["created"],
        "url": metadata["url"],
        "files": "; ".join(str(path.relative_to(folder)) for path in paths.values()),
    }
    for old in rows:
        if old.get("thread_id") == item["thread_id"]:
            # При повторном запуске можно добавить новые форматы файлов:
            # обновим перечень, не дублируя строку с этой темой.
            old_files = [x for x in old.get("files", "").split("; ") if x]
            new_files = [x for x in item["files"].split("; ") if x]
            item["files"] = "; ".join(dict.fromkeys(old_files + new_files))
            if all(old.get(key) == item.get(key) for key in fieldnames):
                return
            old.update(item)
            break
    else:
        rows.append(item)

    temp = index_path.with_suffix(".csv.part")
    try:
        with temp.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        temp.replace(index_path)
    finally:
        if temp.exists():
            temp.unlink()


# ---------------------------- СОХРАНЕНИЕ ------------------------------------

def make_metadata(thread, category, row):
    creator = getattr(thread, "creator", None)
    created_unix = getattr(thread, "create_date", None) or row.get("created_date")
    return {
        "title": thread.title, "thread_id": thread.id, "url": thread.url,
        "category": category.title, "category_id": category.id,
        "category_url": category.url,
        "author": getattr(creator, "username", None) or row.get("username_author") or "неизвестно",
        "author_id": getattr(creator, "id", None),
        "created": readable_date(created_unix), "created_unix": created_unix,
        "prefix": thread.prefix or row.get("prefix") or "отсутствует",
        "pinned": bool(row.get("is_pinned", False)),
        "closed": bool(thread.is_closed),
        "first_post_id": thread.thread_post_id, "pages_count": thread.pages_count,
        "last_reply": readable_date(row.get("last_message_date")),
        "last_reply_author": row.get("username_last_message") or "неизвестно",
    }


def shown_metadata(metadata):
    if not INCLUDE_METADATA:
        return {}
    return {field: metadata.get(field) for field in METADATA_FIELDS}


def shown_value(value):
    if value is None:
        return "неизвестно"
    if isinstance(value, bool):
        return "да" if value else "нет"
    return str(value)


def render_txt(metadata, posts):
    sections = []
    if INCLUDE_METADATA:
        sections.append("\n".join(f"{FIELD_LABELS[k]}: {shown_value(v)}" for k, v in shown_metadata(metadata).items()))
    for number, post in enumerate(posts, start=1):
        lines = [f"{TXT_SEPARATOR}\n{'Первое сообщение' if number == 1 else 'Ответ #' + str(number - 1)}\n{TXT_SEPARATOR}"]
        if INCLUDE_POST_INFO:
            lines.extend(f"{POST_LABELS[k]}: {shown_value(post.get(k))}" for k in POST_LABELS)
        for kind, content in post["content"].items():
            lines.append(f"\n--- {kind.upper()} ---\n{content}")
        sections.append("\n".join(lines))
    return "\n\n".join(part for part in sections if part).rstrip() + "\n"


def render_md(metadata, posts):
    title = str(metadata["title"]).replace("\n", " ")
    sections = [f"# {title}"]
    if INCLUDE_METADATA:
        sections.extend(f"**{FIELD_LABELS[k]}:** {shown_value(v)}  " for k, v in shown_metadata(metadata).items())
    for number, post in enumerate(posts, start=1):
        sections.append(f"\n## {'Первое сообщение' if number == 1 else 'Ответ #' + str(number - 1)}")
        if INCLUDE_POST_INFO:
            sections.extend(f"**{POST_LABELS[k]}:** {shown_value(post.get(k))}  " for k in POST_LABELS)
        for kind, content in post["content"].items():
            # Динамический fence, чтобы содержимое с ``` не ломало Markdown.
            fence = "`" * max(3, max((len(m.group(0)) for m in re.finditer(r"`+", content)), default=0) + 1)
            sections.append(f"\n### {kind.upper()}\n\n{fence}{kind if kind != 'text' else 'text'}\n{content}\n{fence}\n")
    return "\n".join(sections).rstrip() + "\n"


def render_json(metadata, posts):
    return json.dumps({"metadata": shown_metadata(metadata), "posts": posts}, ensure_ascii=False, indent=2) + "\n"


def save_files(paths, metadata, posts):
    outputs = {
        "txt": lambda: render_txt(metadata, posts),
        "md": lambda: render_md(metadata, posts),
        "json": lambda: render_json(metadata, posts),
    }
    for ext, path in paths.items():
        if path.exists() and not OVERWRITE_EXISTING:
            continue
        temp = path.with_suffix(path.suffix + ".part")
        try:
            temp.write_text(outputs[ext](), encoding=ENCODING)
            temp.replace(path)
        finally:
            if temp.exists():
                temp.unlink()


async def get_post_content(forum_api, thread, post_id, content_types, post=None):
    # Первый пост не загружаем отдельно для HTML/текста — они уже в Thread.
    is_first = int(post_id) == int(thread.thread_post_id)
    if not is_first and post is None:
        post = await retry_call(f"сообщение {post_id}", lambda: forum_api.get_post(int(post_id)))
    source = thread if is_first else post
    content = {}
    if "bbcode" in content_types:
        # Для первого сообщения используется get_post_bbcode(). Для ответов
        # — post.bbcode_content(). В обоих случаях работает штатная библиотека.
        bbcode = await retry_call(
            f"BBCode сообщения {post_id}",
            (lambda: forum_api.get_post_bbcode(int(thread.id), int(post_id))) if is_first
            else (lambda: post.bbcode_content()),
            is_valid=lambda value: isinstance(value, str) and bool(value.strip()),
        )
        content["bbcode"] = bbcode
    if "html" in content_types:
        content["html"] = getattr(source, "html_content", "") or ""
    if "text" in content_types:
        content["text"] = getattr(source, "text_content", "") or ""
    creator = getattr(source, "creator", None)
    return {
        "post_id": int(post_id),
        "author": getattr(creator, "username", None) or "неизвестно",
        "author_id": getattr(creator, "id", None),
        "created": readable_date(getattr(source, "create_date", None)),
        "url": (getattr(source, "url", None) if not is_first else f"{thread.url.rstrip('/')}/#post-{post_id}"),
        "content": content,
    }


async def export_thread(forum_api, category, row, folder, files_folder, formats, content_types, stats):
    tid = row_id(row)
    if tid <= 0:
        stats["failed"] += 1
        write_error(folder, category.id, f"Некорректный ID в записи темы: {row!r}")
        return
    try:
        thread = await retry_call(f"тема {tid}", lambda: forum_api.get_thread(tid))
        if not thread.thread_post_id:
            raise RuntimeError("Не определён ID первого сообщения темы")
        paths = make_file_paths(thread, category, files_folder, formats)
        if not OVERWRITE_EXISTING and all(path.is_file() for path in paths.values()):
            add_to_index(folder, category.id, make_metadata(thread, category, row), paths)
            stats["skipped"] += 1
            print(f"  [=] {thread.id} — уже сохранена")
            return

        metadata = make_metadata(thread, category, row)
        posts = [await get_post_content(forum_api, thread, thread.thread_post_id, content_types)]
        if INCLUDE_REPLIES:
            ids = await retry_call(
                f"список сообщений темы {tid}",
                lambda: forum_api.get_all_thread_posts(tid),
                is_valid=lambda value: isinstance(value, list) and len(value) > 0,
            )
            for post_id in dict.fromkeys(str(item) for item in ids):
                if not post_id.isdecimal() or int(post_id) == int(thread.thread_post_id):
                    continue
                posts.append(await get_post_content(forum_api, thread, int(post_id), content_types))

        save_files(paths, metadata, posts)
        add_to_index(folder, category.id, metadata, paths)
        stats["saved"] += 1
        print(f"  [+] {thread.id} — {thread.title[:80]} ({', '.join(formats)})")
    except Exception as error:
        stats["failed"] += 1
        message = f"Тема {tid}: {type(error).__name__}: {error}"
        print(f"  [X] {message}")
        write_error(folder, category.id, message)


# -------------------------- СБОР КАТЕГОРИЙ ----------------------------------

async def export_category(forum_api, category_id, root, formats, content_types, visited, stats):
    if category_id in visited:
        return
    visited.add(category_id)
    try:
        category = await retry_call(f"категория {category_id}", lambda: forum_api.get_category(category_id))
    except Exception as error:
        stats["failed"] += 1
        print(f"[X] Не открыть категорию {category_id}: {error}")
        return

    folder, files_folder = prepare_paths(category, root)
    write_category_info(category, folder)
    print(f"\nКатегория: {category.title} (ID {category.id}); страниц: {category.pages_count}")
    seen_threads = set()
    previous_page_ids = None
    selected = 0
    page = 1

    while True:
        if MAX_PAGES_PER_CATEGORY and page > MAX_PAGES_PER_CATEGORY:
            print("  Достигнут заданный лимит страниц.")
            break
        if page > 10000:
            stats["failed"] += 1
            write_error(folder, category.id, "Достигнут защитный лимит 10000 страниц")
            break
        try:
            response = await retry_call(
                f"категория {category.id}, страница {page}",
                lambda p=page: category.get_threads_extended(page=p),
            )
            rows = list_rows(response)
        except Exception as error:
            stats["failed"] += 1
            write_error(folder, category.id, f"Не удалось получить страницу {page}: {error}")
            print(f"  [X] Не удалось загрузить страницу {page} (категория неполная)")
            break

        page_ids = tuple(row_id(row) for row in rows if row_id(row) > 0)
        if not page_ids or page_ids == previous_page_ids:
            break
        previous_page_ids = page_ids
        new_rows = []
        for row in rows:
            tid = row_id(row)
            if tid <= 0 or tid in seen_threads:
                continue
            seen_threads.add(tid)
            if choose_row(row):
                new_rows.append(row)
        if not new_rows:
            # Некоторые закреплённые темы могут повторяться на каждой странице.
            # Поэтому, пока есть непрочитанные страницы, не прерываем обход.
            if page >= max(int(category.pages_count or 1), 1):
                break
            page += 1
            continue

        print(f"Страница {page}: новых подходящих тем {len(new_rows)}")
        for row in new_rows:
            if MAX_THREADS_PER_CATEGORY and selected >= MAX_THREADS_PER_CATEGORY:
                break
            selected += 1
            await export_thread(forum_api, category, row, folder, files_folder, formats, content_types, stats)
        if MAX_THREADS_PER_CATEGORY and selected >= MAX_THREADS_PER_CATEGORY:
            print("  Достигнут заданный лимит тем.")
            break
        page += 1

    if INCLUDE_SUBCATEGORIES:
        try:
            children = await retry_call(
                f"подразделы {category.id}", lambda: category.get_categories(),
                is_valid=lambda value: isinstance(value, list),
            )
            for child in children:
                if str(child).isdecimal():
                    await export_category(forum_api, int(child), root, formats, content_types, visited, stats)
        except Exception as error:
            stats["failed"] += 1
            write_error(folder, category.id, f"Подразделы не загружены: {error}")


# ------------------------------ ЗАПУСК ---------------------------------------

async def main():
    try:
        formats, content_types = normalize_settings()
        category_ids = parse_ids(CATEGORY_IDS or input("Введите ID категорий через пробел/запятую: "))
    except (ValueError, KeyError) as error:
        print(f"Ошибка настроек: {error}")
        return

    cookies = dict(COOKIES)
    for key in ("xf_user", "xf_tfa_trust"):
        if not cookies.get(key) or cookies[key] == "your":
            cookies[key] = getpass.getpass(f"Cookie {key}: ").strip()
    if not cookies.get("xf_user") or not cookies.get("xf_tfa_trust"):
        print("Необходимо указать cookie xf_user и xf_tfa_trust.")
        return

    root = Path(OUTPUT_DIR).expanduser()
    if not root.is_absolute():
        root = Path(__file__).resolve().parent / root

    # Очередь встроена в Arizona-Forum-API-Async, выполняем ВСЕ вызовы
    # последовательно (никаких gather/create_task/semaphore).
    queue = arz_api.RequestQueue(
        interval=REQUEST_INTERVAL_SECONDS,
        max_requests=MAX_REQUESTS_PER_MINUTE,
        window_seconds=60.0,
    )
    forum_api = arz_api.ArizonaForumAPI(cookie=cookies, request_queue=queue)
    stats = {"saved": 0, "skipped": 0, "failed": 0}

    try:
        await forum_api.connect()
        print("Успешно подключились!")
        root.mkdir(parents=True, exist_ok=True)
        visited = set()
        for category_id in category_ids:
            await export_category(forum_api, category_id, root, formats, content_types, visited, stats)
    except arz_api.IncorrectLoginData:
        print("Ошибка: неверные cookies или сессия истекла.")
    except Exception as error:
        print(f"Произошла ошибка: {type(error).__name__}: {error}")
    finally:
        await forum_api.close()
        print(f"\nГотово! Сохранено: {stats['saved']}, пропущено: {stats['skipped']}, "
              f"ошибок: {stats['failed']}.")
        print(f"Папка с файлами: {root}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановлено пользователем. Готовые файлы сохранены.")