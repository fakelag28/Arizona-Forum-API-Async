# Arizona Forum API Async

[![PyPI version](https://img.shields.io/pypi/v/arizona-forum-api-async.svg)](https://pypi.org/project/arizona-forum-api-async/)
[![Python Versions](https://img.shields.io/pypi/pyversions/arizona-forum-api-async.svg)](https://pypi.org/project/arizona-forum-api-async/)
[![Downloads](https://static.pepy.tech/badge/arizona-forum-api-async)](https://pepy.tech/project/arizona-forum-api-async)

**Асинхронная Python библиотека для взаимодействия с форумом Arizona RP (forum.arizona-rp.com) без необходимости получения API ключа.**

Эта библиотека предоставляет современный, асинхронный интерфейс для работы с форумом Arizona RP. Это расширенная и улучшенная **асинхронная** версия оригинальной библиотеки [Arizona-API](https://github.com/TastyBread123/Arizona-API) от [TastyBread123](https://www.blast.hk/members/455219/), построенная с использованием `aiohttp`.

---

## Ключевые особенности

*   **Полностью асинхронная:** Построена с использованием `asyncio` и `aiohttp`.
*   **Не требует API ключа:** Взаимодействует с форумом, имитируя запросы браузера, что избавляет от необходимости получать официальные ключи XenForo API.
*   **Обширная функциональность:** Поддерживает около 48 методов.
*   **Объектно-ориентированные модели:** Представляет сущности форума, такие как `Member`, `Thread`, `Post`, `Category`, в виде Python объектов с соответствующими методами.
*   **Простота использования:** Предоставляет чистую и интуитивно понятную структуру API.

---

## Установка и обновление

Установите или обновите библиотеку напрямую из PyPI:

```bash
pip install arizona-forum-api-async
```

Для обновления:

```bash
pip install --upgrade arizona-forum-api-async
```

Если хотите собрать библиотеку вручную:

1. Скачайте репозиторий и перейдите в него:

```bash
git clone https://github.com/fakelag28/Arizona-Forum-API-Async.git
cd Arizona-Forum-API-Async
```

2. Обновите инструменты сборки и соберите дистрибутив:

```bash
python -m pip install --upgrade pip setuptools wheel build
python -m build
python -m pip install dist/*.whl
```

Можно пропустить сборку и сразу установить:

```bash
python -m pip install .
```

---

## Аутентификация и настройка

Поскольку эта библиотека имитирует действия залогиненного пользователя, вам потребуются Cookie из вашей браузерной сессии на `forum.arizona-rp.com`:
<img src="https://github.com/fakelag28/Arizona-Forum-API-Async/blob/main/repo_images/cookie_guide.png?raw=true">

**Как их получить:**

1.  Войдите в свой форумный аккаунт на `forum.arizona-rp.com`;
2.  Установите двухфакторную аутентификацию и перезайдите в свой аккаунт;
3.  Установите расширение ["Cookie Editor"](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm), после чего с его помощью получите следующие значения:
* xf_tfa_trust
* xf_user


---

## Документация и примеры

*   **[Папка с примерами](https://github.com/fakelag28/Arizona-Forum-API-Async/tree/main/examples):** Практические примеры, демонстрирующие различные возможности библиотеки.

---

## Лицензия

Этот проект лицензирован под **MIT License**.