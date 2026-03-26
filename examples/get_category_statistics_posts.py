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

        statistics = await forum_api.get_category_statistics_posts(634, duration="day")
        print(json.dumps(statistics, indent=4, ensure_ascii=False))
    except arz_api.IncorrectLoginData:
        print("Error: invalid cookies or expired session.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await forum_api.close()


if __name__ == "__main__":
    asyncio.run(main())
