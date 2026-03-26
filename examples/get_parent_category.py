import asyncio
import arizona_forum_async as arz_api


async def main():
    cookies = {"xf_user": "your",
              "xf_tfa_trust": "your"}

    forum_api = arz_api.ArizonaForumAPI(cookie=cookies)

    try:
        await forum_api.connect()
        print("Successfully connected!")

        parent_category = await forum_api.get_parent_category_of_category(540)
        if parent_category:
            print(
                f"Parent category: {parent_category.title} ({parent_category.id})\n"
                f"Pages: {parent_category.pages_count}"
            )
        else:
            print("Parent category not found.")
    except arz_api.IncorrectLoginData:
        print("Error: invalid cookies or expired session.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await forum_api.close()


if __name__ == "__main__":
    asyncio.run(main())
