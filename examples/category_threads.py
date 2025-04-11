import asyncio
import arizona_forum_async as arz_api

async def main():
    cookies = {"xf_user": "1058071%2Cpyl5mfwp27ag59SwiBEmyB58uZ2OFqW3KFGoFaf4",
              "xf_tfa_trust": "fifcs_70CGMxlGN6y6dofRwSR6M7LtLS", 
              "xf_session": "OmIBQ19cobJRq47LHiT4U4gUmtGWseyp"}

    api = arz_api.ArizonaAPI(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 YaBrowser/24.12.0.0 Safari/537.36", cookie=cookies)

    try:
        await api.connect()
        print("Успешно подключились!")

        category = await api.get_category(354)
        if category:
            threads = await category.get_threads()
            
            print('Закрепленные темы:')
            for i in threads["pins"]:
                thread = await api.get_thread(i)
                print(f'{thread.title} by {thread.creator.username}')

            print('\n____________________\nНезакрепленные темы:')
            for i in threads["unpins"]:
                thread = await api.get_thread(i)
                print(f'{thread.title} by {thread.creator.username}')

    except arz_api.IncorrectLoginData:
        print("Ошибка: Неверные куки или сессия истекла.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(main())
