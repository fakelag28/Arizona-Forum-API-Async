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
*   **Обширная функциональность:** Поддерживает около 38 методов.
*   **Объектно-ориентированные модели:** Представляет сущности форума, такие как `Member`, `Thread`, `Post`, `Category`, в виде Python объектов с соответствующими методами.
*   **Простота использования:** Предоставляет чистую и интуитивно понятную структуру API.

---

## Установка

Установите библиотеку напрямую из PyPI:

```bash
pip install arizona-forum-api-async
```

---

## Аутентификация и настройка

Поскольку эта библиотека имитирует действия залогиненного пользователя, вам потребуются две вещи из вашей браузерной сессии на `forum.arizona-rp.com`:

1.  **User Agent:** Строка User Agent вашего браузера.
2.  **Cookies:** Cookies вашей сессии на форуме.

**Как их получить:**

1.  Войдите в свой форумный аккаунт на `forum.arizona-rp.com`.
2.  Установите расширение "Cookie Editor", после чего с его помощью получите следующие значения:
* xf_session
* xf_tfa_trust
* xf_user
3. Узнайте свой User Agent браузера или используйте любые другие из интернета.

---

## Документация и примеры

*   **[Wiki (Расширенная документация синхронной версии)](https://github.com/fakelag28/Arizona-Forum-API-Extended/wiki/Основная-документация):** Подробная документация для другой [расширенной синхронной версии](https://github.com/fakelag28/Arizona-Forum-API-Extended/).
*   **[Документация оригинальной библиотеки](https://tastybread123.github.io/Arizona-API/arz_api.html):** Документация для оригинальной синхронной библиотеки.
*   **[Папка с примерами](https://github.com/fakelag28/Arizona-Forum-API-Async/tree/main/examples):** Практические примеры, демонстрирующие различные возможности библиотеки.