import asyncio
import arizona_forum_async as arz_api
from datetime import datetime

THREAD_ID = 10331084

COOKIES = {"xf_user": "your",
              "xf_tfa_trust": "your"}

MESSAGE_TEXT = """[CENTER][FONT=verdana][IMG]https://i.postimg.cc/ZKSPqNwF/14115119429-OPSNP7-867.png[/IMG]
[SIZE=6][COLOR=rgb(209, 72, 65)][B]ИТОГИ КОНКУРСА[/B][/COLOR][/SIZE][/FONT]
[/CENTER]
[TABLE width="100%"]
[TR]
[td][CENTER][SIZE=3][FONT=verdana][B][COLOR=rgb(209, 72, 65)]МЕСТО[/COLOR][/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B][COLOR=rgb(209, 72, 65)]НИКНЕЙМ[/COLOR][/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B][COLOR=rgb(209, 72, 65)]РЕЗУЛЬТАТ[/COLOR][/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B][COLOR=rgb(209, 72, 65)]ПРИЗ[/COLOR][/B][/FONT][/SIZE][/CENTER][/td]
[/TR]
[TR]
[td][CENTER]🥇[SIZE=3][FONT=verdana][B] 1[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]Artik_Stealer[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]7950 баллов[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B][COLOR=rgb(44, 182, 115)]1.000.000.000$[/COLOR][/B][/FONT][/SIZE][/CENTER][/td]
[/TR]
[TR]
[td][CENTER]🥈[SIZE=3][FONT=verdana][B] 2[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]Richard_Carters[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]4965 баллов[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B][COLOR=rgb(44, 182, 115)]750.000.000$[/COLOR][/B][/FONT][/SIZE][/CENTER][/td]
[/TR]
[TR]
[td][CENTER]🥉[SIZE=3][FONT=verdana][B] 3[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]Donat_Hokage[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]3300 баллов[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B][COLOR=rgb(44, 182, 115)]500.000.000$[/COLOR][/B][/FONT][/SIZE][/CENTER][/td]
[/TR]
[TR]
[td][CENTER][SIZE=3][FONT=verdana][B]4[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]Null_Hellsing[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]2400 баллов[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B][COLOR=rgb(44, 182, 115)]350.000.000$[/COLOR][/B][/FONT][/SIZE][/CENTER][/td]
[/TR]
[TR]
[td][CENTER][SIZE=3][FONT=verdana][B]5[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]Alexander_Tyrk[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]2125 баллов[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B][COLOR=rgb(44, 182, 115)]350.000.000$[/COLOR][/B][/FONT][/SIZE][/CENTER][/td]
[/TR]
[TR]
[td][CENTER][SIZE=3][FONT=verdana][B]6[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]Ivan_Genadievich[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B]1850 баллов[/B][/FONT][/SIZE][/CENTER][/td]
[td][CENTER][SIZE=3][FONT=verdana][B][COLOR=rgb(44, 182, 115)]250.000.000$[/COLOR][/B][/FONT][/SIZE][/CENTER][/td]
[/TR]
[/TABLE]

[CENTER][SIZE=5][FONT=verdana][COLOR=rgb(209, 72, 65)][B]СПЕЦИАЛЬНЫЕ НОМИНАЦИИ[/B][/COLOR][/FONT][/SIZE]
[SIZE=3][FONT=verdana][B][COLOR=rgb(255, 255, 255)]🎬 "Лучший сюжет" — [/COLOR][/B][URL='https://youtu.be/eOX3t5fHAkk?si=dxR9_fPPOlWZGl2y'][B][COLOR=rgb(255, 255, 255)]Richard_Carters [/COLOR][/B][/URL][B][COLOR=rgb(255, 255, 255)]— 100.000.000$[/COLOR]
[COLOR=rgb(255, 255, 255)]🛡️ "Лучшая операция" [SIZE=3][FONT=verdana][B][COLOR=rgb(255, 255, 255)]— [/COLOR][/B][/FONT][/SIZE][/COLOR][/B][URL='https://www.youtube.com/watch?v=4BDtqweGFnw'][B][COLOR=rgb(255, 255, 255)]Null_Hellsing [/COLOR][/B][/URL][B][COLOR=rgb(255, 255, 255)]— 100.000.000$[/COLOR]
[COLOR=rgb(255, 255, 255)]⚙️ "Техническое совершенство"[SIZE=3][FONT=verdana][URL='https://www.youtube.com/watch?v=4BDtqweGFnw'][B][COLOR=rgb(255, 255, 255)] [/COLOR][/B][/URL][B][COLOR=rgb(255, 255, 255)]— [/COLOR][/B][/FONT][/SIZE]никто не забирает[/COLOR][/B][/FONT][/SIZE]

[COLOR=rgb(255, 255, 255)][B][FONT=verdana]Поздравляем победителей и благодарим всех за участие! ❄️[/FONT]
[FONT=verdana]По поводу получения вознаграждений обращаться к Steven Vels (Discord: Hellich.) [/FONT][/B][/COLOR][/CENTER]"""


async def check_and_post():
    api = arz_api.ArizonaForumAPI(user_agent="user_agent", cookie=COOKIES)
    posted = False
    
    try:
        await api.connect()
        print("Успешно подключились к форуму!")
        
        while not posted:
            now = datetime.now()
            
            if now.month == 1 and now.day == 1 and now.hour == 0 and now.minute == 0:
                print(f"🎉 Наступил Новый Год! Публикуем сообщение...")
                
                message_html = MESSAGE_TEXT.replace('\n', '<br>')
                response = await api.answer_thread(THREAD_ID, message_html)
                print(f"Сообщение успешно опубликовано! Статус: {response.status}")
                posted = True
            else:
                target = datetime(now.year + 1 if now.month == 12 else now.year, 1, 1, 0, 0, 0)
                remaining = target - now
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Ожидание Нового Года... Осталось: {hours}ч {minutes}м {seconds}с")
                await asyncio.sleep(25)
                
    except arz_api.IncorrectLoginData:
        print("Ошибка: Неверные куки или сессия истекла.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await api.close()
        print("Соединение закрыто.")


if __name__ == "__main__":
    print("Скрипт новогоднего поздравления запущен!")
    print(f"ID темы для публикации: {THREAD_ID}")
    print("-" * 50)
    asyncio.run(check_and_post())
