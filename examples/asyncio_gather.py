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

        category = await api.get_category(354)
        if category:
            threads = await category.get_threads()
            
            tasks = []
            for i in threads["pins"] + threads["unpins"]:
                tasks.append(api.get_thread(i))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            print('Закрепленные темы:')
            for thread in results[:len(threads["pins"])]:
                if not isinstance(thread, Exception):
                    print(f'{thread.title} by {thread.creator.username}')

            print('\n____________________\nНезакрепленные темы:')
            for thread in results[len(threads["pins"]):]:
                if not isinstance(thread, Exception):
                    print(f'{thread.title} by {thread.creator.username}')

    except arz_api.IncorrectLoginData:
        print("Ошибка: Неверные куки или сессия истекла.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(main())