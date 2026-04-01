import asyncio
import json
import arizona_forum_async as arz_api


async def main():
    cookies = {"xf_user": "your",
              "xf_tfa_trust": "your"}

    forum_api = arz_api.ArizonaForumAPI(cookie=cookies)

    try:
        await forum_api.connect()
        print("Successfully connected!")

        # Пример получения тем из категории с голосованием (ID 3933)
        print("\n=== Получение тем из категории с голосованием ===")
        threads = await forum_api.get_threads_from_vote_category(3933, page=1)
        if threads:
            print(f"Найдено тем: {len(threads)}")
            print(json.dumps(threads, indent=4, ensure_ascii=False))
        else:
            print("Не удалось получить темы из категории")

        # Пример получения детальной информации о теме с голосованием
        print("\n=== Получение детальной информации о теме с голосованием ===")
        if threads and len(threads) > 0:
            first_thread_id = threads[0]['thread_id']
            thread_detail = await forum_api.get_vote_thread_detail(first_thread_id)
            if thread_detail:
                print(f"Тема ID: {thread_detail['thread_id']}")
                print(f"Количество голосов: {thread_detail['votes_count']}")
                if thread_detail['first_post']:
                    print(f"Автор: {thread_detail['first_post']['author_username']}")
                    print(f"Дата публикации: {thread_detail['first_post']['posted_date_str']}")
                    print(f"Сервер: {thread_detail['first_post'].get('server', 'N/A')}")
                print("\nПолные данные:")
                print(json.dumps(thread_detail, indent=4, ensure_ascii=False))
            else:
                print(f"Не удалось получить информацию о теме {first_thread_id}")
        else:
            # Пример для конкретной темы
            thread_detail = await forum_api.get_vote_thread_detail(10850153)
            if thread_detail:
                print(f"Тема ID: {thread_detail['thread_id']}")
                print(f"Количество голосов: {thread_detail['votes_count']}")
                if thread_detail['first_post']:
                    print(f"Автор: {thread_detail['first_post']['author_username']}")
                    print(f"Дата публикации: {thread_detail['first_post']['posted_date_str']}")
                print("\nПолные данные:")
                print(json.dumps(thread_detail, indent=4, ensure_ascii=False))

    except arz_api.IncorrectLoginData:
        print("Error: invalid cookies or expired session.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await forum_api.close()


if __name__ == "__main__":
    asyncio.run(main())
