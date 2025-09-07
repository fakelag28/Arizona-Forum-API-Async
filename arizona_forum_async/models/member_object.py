from bs4 import BeautifulSoup
import aiohttp
from re import compile
from typing import TYPE_CHECKING

from arizona_forum_async.consts import MAIN_URL

if TYPE_CHECKING:
    from arizona_forum_async.api import ArizonaAPI


class Member:
    def __init__(self, API : 'ArizonaAPI', id: int, username: str, user_title: str, avatar: str, roles: list, activity: str, messages_count: int, reactions_count: int, trophies_count: int, username_color: str) -> None:
        self.API = API
        self.id = id
        """**ID пользователя**"""
        self.username = username
        """**Имя пользователя**"""
        self.user_title = user_title
        """**Звание пользователя**"""
        self.avatar = avatar
        """**Ссылка на аватарку пользователя**"""
        self.roles = roles
        """Роль пользователя на форуме ('покраска')"""
        self.activity = activity
        """**Активность пользователя на форуме**"""
        self.messages_count = messages_count
        """**Количество сообщений в счетчике**"""
        self.reactions_count = reactions_count
        """**Количество реакций в счетчике**"""
        self.trophies_count = trophies_count
        """**Количество баллов в счетчике**"""

        self.username_color = username_color

        self.url = f"{MAIN_URL}/members/{self.id}/"
        """Ссылка на объект"""
        

    async def follow(self) -> aiohttp.ClientResponse:
        """Изменить статус подписки на пользователя
        
        Returns:
            Объект Response модуля requests
        """

        return await self.API.follow_member(self.id)
    
    async def ignore(self) -> aiohttp.ClientResponse:
        """Изменить статус игнорирования пользователя
        
        Returns:
            Объект Response модуля requests
        """

        return await self.API.ignore_member(self.id)
    
    async def add_message(self, message_html: str) -> aiohttp.ClientResponse:
        """Отправить сообщение на стенку пользователя

        Attributes:
            message_html (str): Текст сообщения. Рекомендуется использование HTML
            
        Returns:
            Объект Response модуля requests
        """

        return await self.API.answer_thread(self.id, message_html)
    
    async def get_profile_messages(self, page: int = 1) -> list:
        """Возвращает ID всех сообщений со стенки пользователя на странице

        Attributes:
            page (int): Страница для поиска. По умолчанию 1 (необяз.)
            
        Returns:
            Cписок (list) с ID всех сообщений профиля
        """

        return await self.API.get_profile_messages(self.id, page)


class CurrentMember(Member):
    follow = property(doc='Forbidden method for Current Member object')
    ignore = property(doc='Forbidden method for Current Member object')

    async def edit_avatar(self, upload_photo: str) -> aiohttp.ClientResponse:
        """Изменить аватарку пользователя

        Attributes:
            upload_photo (str): Относительный или полный путь до изображения
        
        Returns:
            Объект Response модуля requests
        """

        with open(upload_photo, 'rb') as image:
            file_dict = {'upload': (upload_photo, image.read())}
        
        token = BeautifulSoup(self.API.session.get(f"{MAIN_URL}/help/terms/").content, 'lxml').find('html')['data-csrf']
        data = {
            "avatar_crop_x": 0, 
            "avatar_crop_y": 0,
            "_xfToken": token, 
            "use_custom": 1,
        }
        return await self.API.session.post(f"{MAIN_URL}/account/avatar", files=file_dict, data=data)
    

    async def delete_avatar(self) -> aiohttp.ClientResponse:
        """Удалить автарку пользователя
        
        Returns:
            Объект Response модуля requests
        """
        token = BeautifulSoup(self.API.session.get(f"{MAIN_URL}/help/terms/").content, 'lxml').find('html')['data-csrf']
        file_dict = {'upload': ("", "")}
        data = {
            "avatar_crop_x": 0, 
            "avatar_crop_y": 0,
            "_xfToken": token, 
            "use_custom": 1,
            "delete_avatar": 1
        }

        return await self.API.session.post(f"{MAIN_URL}/account/avatar", files=file_dict, data=data)
