import aiohttp
from typing import TYPE_CHECKING
from arizona_forum_async.consts import MAIN_URL

if TYPE_CHECKING:
    from arizona_forum_async import ArizonaAPI
    from arizona_forum_async.models import Member, Thread


class Post:
    def __init__(self, API: 'ArizonaAPI', id: int, creator: 'Member', thread: 'Thread', create_date: int, html_content: str, text_content: str) -> None:
        self.API = API
        self.id = id
        """**ID сообщения**"""
        self.creator = creator
        """**Объект Member отправителя сообщения**"""
        self.thread = thread
        """**Объект Thread темы, в которой оставлено сообщение**"""
        self.create_date = create_date
        """**Дата отправки сообщения в UNIX**"""
        self.html_content = html_content
        """**Сырое содержимое сообщения**"""
        self.text_content = text_content
        """**Текст из сообщения**"""
        self.url = f"{MAIN_URL}/posts/{self.id}/"
        """Ссылка на объект"""

    async def bbcode_content(self) -> aiohttp.ClientResponse:
        """Получить bbcode поста
            
        Returns:
            Str текст bbcode
        """

        return await self.API.get_post_bbcode(self.thread.id, self.id)

    async def react(self, reaction_id: int = 1) -> aiohttp.ClientResponse:
        """Поставить реакцию на сообщение

        Attributes:
            reaction_id (int): ID реакции. По умолчанию 1 (необяз.)
            
        Returns:
            Объект Response модуля requests
        """

        return await self.API.react_post(self.id, reaction_id)
    

    async def edit(self, message_html: str) -> aiohttp.ClientResponse:
        """Отредактировать сообщение

        Attributes:
            message_html (str): Новое содержание сообщения. Рекомендуется использование HTML
        
        Returns:
            Объект Response модуля requests
        """

        return await self.API.edit_post(self.id, message_html)


    async def delete(self, reason: str, hard_delete: bool = False) -> aiohttp.ClientResponse:
        """Удалить сообщение

        Attributes:
            reason (str): Причина для удаления
            hard_delete (bool): Полное удаление сообщения. По умолчанию False (необяз.)
            
        Returns:
            Объект Response модуля requests
        """

        return await self.API.delete_post(self.id, reason, hard_delete)
    
    
    async def bookmark(self) -> aiohttp.ClientResponse:
        """Добавить сообщение в закладки
        
        Returns:
            Объект Response модуля requests"""
        return await self.API.bookmark_post(self.id)

class ProfilePost:
    def __init__(self, API: 'ArizonaAPI', id: int, creator: 'Member', profile: 'Member', create_date: int, html_content: str, text_content: str) -> None:
        self.API = API
        self.id = id
        """**ID сообщения профиля**"""
        self.creator = creator
        """**Объект Member отправителя сообщения**"""
        self.profile = profile
        """**Объект Member профиля, в котором оставлено сообщение**"""
        self.create_date = create_date
        """**Дата отправки сообщения в UNIX**"""
        self.html_content = html_content
        """**Сырое содержимое сообщения**"""
        self.text_content = text_content
        """**Текст из сообщения**"""
        self.url = f"{MAIN_URL}/profile-posts/{self.id}/"
        """Ссылка на объект"""

    async def react(self, reaction_id: int = 1) -> aiohttp.ClientResponse:
        """Поставить реакцию на сообщение профиля

        Attributes:
            reaction_id (int): ID реакции. По умолчанию 1 (необяз.)
            
        Returns:
            Объект Response модуля requests
        """

        return await self.API.react_profile_post(self.id, reaction_id)


    async def comment(self, message_html: str) -> aiohttp.ClientResponse:
        """Прокомментировать сообщение профиля

        Attributes:
            message_html (str): Текст комментария. Рекомендуется использование HTML
        
        Returns:
            Объект Response модуля requests
        """

        return await self.API.comment_profile_post(self.id, message_html)


    async def delete(self, reason: str, hard_delete: bool = False) -> aiohttp.ClientResponse:
        """Удалить сообщение

        Attributes:
            reason (str): Причина для удаления
            hard_delete (bool): Полное удаление сообщения. По умолчанию False (необяз.)
            
        Returns:
            Объект Response модуля requests
        """

        return await self.API.delete_profile_post(self.id, reason, hard_delete)
    

    async def edit(self, message_html: str) -> aiohttp.ClientResponse:
        """Отредактировать сообщение профиля

        Attributes:
            message_html (str): Новое содержание сообщения профиля. Рекомендуется использование HTML
        
        Returns:
            Объект Response модуля requests
        """

        return await self.API.edit_profile_post(self.id, message_html)