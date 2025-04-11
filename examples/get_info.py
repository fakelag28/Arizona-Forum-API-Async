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

        # Получаем текущего пользователя
        user = await api.get_current_member()
        if user:
            print(f'Успешно авторизовались!\nИмя пользователя: {user.username} | Звание: {user.user_title}\nАватарка: {user.avatar}\nСообщений: {user.messages_count} | Реакций: {user.reactions_count}\n')

        # Получаем категорию
        category = await api.get_category(1865)
        if category:
            print(f"Название: {category.title} ({category.id})\nСтраниц: {category.pages_count}\n")

        # Получаем пользователя по ID
        member = await api.get_member(583439)
        if member:
            print(f'Пользователь найден!\nИмя пользователя: {member.username} | Звание: {member.user_title}\nАватарка: {member.avatar}\nСообщений: {member.messages_count} | Реакций: {member.reactions_count} | Баллов: {member.trophies_count}\n')

        # Получаем тему
        thread = await api.get_thread(6594323)
        if thread:
            print(f'Название: {thread.title} ({thread.id})\nАвтор темы: {thread.creator.username}\nДата создания: {thread.create_date} | Закрыто: {thread.is_closed}')

        # Получаем статистику форума
        statistic = await api.get_forum_statistic()
        if statistic:
            print(f'\n\nТем: {statistic.threads_count} | Постов: {statistic.posts_count} | Пользователей: {statistic.users_count}\nПоследний пользователь: {statistic.last_register_member.username}')

        # Получаем пост
        post = await api.get_post(36550558)
        if post:
            print(f'\n\nАвтор: {post.creator.username}({post.creator.id})\nID: {post.id} | Дата создания: {post.create_date}\nРазмещено в теме {post.thread.title}\n\n{post.bb_content}')

        # Получаем профильный пост
        profile_post = await api.get_profile_post(2247012)
        if profile_post:
            print(f"\n\nАвтор: {profile_post.creator.username} ({profile_post.creator.id})\nСоздано в {profile_post.create_date} у пользователя {profile_post.profile.username} ({profile_post.profile.id})\n\n{profile_post.bb_content}")

    except arz_api.IncorrectLoginData:
        print("Ошибка: Неверные куки или сессия истекла.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(main())
