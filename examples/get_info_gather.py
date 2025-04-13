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

        # Создаем задачи для всех запросов
        tasks = [
            api.get_current_member(),
            api.get_category(1865),
            api.get_member(583439),
            api.get_thread(6594323),
            api.get_forum_statistic(),
            api.get_post(36550558),
            api.get_profile_post(2247012)
        ]

        # Запускаем все задачи одновременно
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Обрабатываем результаты
        user, category, member, thread, statistic, post, profile_post = results

        if user and not isinstance(user, Exception):
            print(f'Успешно авторизовались!\nИмя пользователя: {user.username} | Звание: {user.user_title}\nАватарка: {user.avatar}\nСообщений: {user.messages_count} | Реакций: {user.reactions_count}\n')

        if category and not isinstance(category, Exception):
            print(f"Название: {category.title} ({category.id})\nСтраниц: {category.pages_count}\n")

        if member and not isinstance(member, Exception):
            print(f'Пользователь найден!\nИмя пользователя: {member.username} | Звание: {member.user_title}\nАватарка: {member.avatar}\nСообщений: {member.messages_count} | Реакций: {member.reactions_count} | Баллов: {member.trophies_count}\n')

        if thread and not isinstance(thread, Exception):
            print(f'Название: {thread.title} ({thread.id})\nАвтор темы: {thread.creator.username}\nДата создания: {thread.create_date} | Закрыто: {thread.is_closed}')

        if statistic and not isinstance(statistic, Exception):
            print(f'\n\nТем: {statistic.threads_count} | Постов: {statistic.posts_count} | Пользователей: {statistic.users_count}\nПоследний пользователь: {statistic.last_register_member.username}')

        if post and not isinstance(post, Exception):
            print(f'\n\nАвтор: {post.creator.username}({post.creator.id})\nID: {post.id} | Дата создания: {post.create_date}\nРазмещено в теме {post.thread.title}\n\n{post.html_content}')

        if profile_post and not isinstance(profile_post, Exception):
            print(f"\n\nАвтор: {profile_post.creator.username} ({profile_post.creator.id})\nСоздано в {profile_post.create_date} у пользователя {profile_post.profile.username} ({profile_post.profile.id})\n\n{profile_post.html_content}")

    except arz_api.IncorrectLoginData:
        print("Ошибка: Неверные куки или сессия истекла.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(main())
