import asyncio
import arizona_forum_async as arz_api
import json

async def main():
    cookies = {"xf_user": "",
              "xf_tfa_trust": "", 
              "xf_session": ""}

    forum_api = arz_api.ArizonaAPI(user_agent="user_agent", cookie=cookies)

    try:
        await forum_api.connect()
        print("Успешно подключились!")

        threads = await forum_api.get_thread_category_detail(634)
        print(json.dumps(threads, indent=4, ensure_ascii=False))
    except arz_api.IncorrectLoginData:
        print("Ошибка: Неверные куки или сессия истекла.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await forum_api.close()

if __name__ == "__main__":
    asyncio.run(main())