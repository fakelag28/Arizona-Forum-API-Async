import asyncio
import arizona_forum_async as arz_api

async def main():
    cookies = {"xf_user": "your",
              "xf_tfa_trust": "your", 
              "xf_session": "your"}

    api = arz_api.ArizonaAPI(user_agent="your", cookie=cookies)

    try:
        await api.connect()
        print("Успешно подключились!")

        # Получаем текущего пользователя асинхронно
        user = await api.get_current_member()
        if user:
            # Получаем сообщения профиля асинхронно
            profile_messages = await user.get_profile_messages()
            
            # Обрабатываем каждое сообщение асинхронно
            for post_id in profile_messages:
                post = await api.get_profile_post(post_id)
                if post:
                    print("\nMessage ID: {0}\nFrom: {1}\nText: {2}\nUnformatted text: {3}".format(
                        post.creator.id, 
                        post.creator.username, 
                        post.text_content, 
                        post.bb_content
                    ))

    except arz_api.IncorrectLoginData:
        print("Ошибка: Неверные куки или сессия истекла.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(main())