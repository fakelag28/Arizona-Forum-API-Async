import asyncio
import arizona_forum_async as arz_api

async def main():
    cookies = {"xf_user": "",
              "xf_tfa_trust": "", 
              "xf_session": ""}

    forum_api = arz_api.ArizonaAPI(user_agent="user_agent", cookie=cookies)

    try:
        await forum_api.connect()
        print("Успешно подключились!")

        post = await forum_api.get_post(42372695)
        bbcode = await post.bbcode_content()
        print(bbcode)
    except arz_api.IncorrectLoginData:
        print("Ошибка: Неверные куки или сессия истекла.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await forum_api.close()

if __name__ == "__main__":
    asyncio.run(main())