import arizona_forum_async as arz_api

cookies = {"xf_user": "your",
              "xf_tfa_trust": "your"}


api = arz_api.ArizonaForumAPI(user_agent="your", cookie=cookies)


# ПРИМЕР ДЛЯ PAYSON
jb = api.send_form(45, {
                   'question[531]': '1',  # Тип жалобы (1 - на адм / 2 - на красных)
                   'question[532]': "Your_Nick",  # Ваш ник
                   'question[533]': "Admin_Nick",  # Ник администратора
                   'question[534]': "ДМ ЗЗ",  # Причина наказания
                   'question[535]': "Суть жалобы",  # Суть жалобы
                   'question[536]': "https://imgur.com/a/Ak1MJWr",  #Скриншот истории наказаний
                   'question[537]': "https://imgur.com/a/Ak1MJWr",  # Скриншот при входе в игру (при бане)
                   'question[538]': "2023-07-10",  # Дата выдачи наказания
                   'question[539]': '1'  # Готов нести ответственность в случае обмана
                   })

print(jb)
