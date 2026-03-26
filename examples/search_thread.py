import asyncio
import arizona_forum_async as arz_api
import json

async def main():
    cookies = {"xf_user": "your",
              "xf_tfa_trust": "your"}

    forum_api = arz_api.ArizonaForumAPI(cookie=cookies)

    try:
        await forum_api.connect()
        print("Успешно подключились!")

        # Асинхронно ищем темы
        threads = await forum_api.search_threads('Nicolas_Reed')
        print(json.dumps(threads, indent=4, ensure_ascii=False))

    except arz_api.IncorrectLoginData:
        print("Ошибка: Неверные куки или сессия истекла.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await forum_api.close()

if __name__ == "__main__":
    asyncio.run(main())