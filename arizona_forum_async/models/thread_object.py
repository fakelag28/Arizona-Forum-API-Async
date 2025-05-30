import aiohttp
from typing import TYPE_CHECKING
from arizona_forum_async.consts import MAIN_URL

if TYPE_CHECKING:
    from arizona_forum_async.models.member_object import Member
    from arizona_forum_async.models.category_object import Category
    from arizona_forum_async import ArizonaAPI


class Thread:
    def __init__(self, API: 'ArizonaAPI', id: int, creator: 'Member', create_date: int, title: str, prefix: str, text_content: str, html_content: str, pages_content: int, thread_post_id: int, is_closed: bool) -> None:
        self.API = API
        self.id = id
        """**ID темы**"""
        self.creator = creator
        """**Объект Member создателя темы**"""
        self.create_date = create_date
        """**Дата создания темы в UNIX**"""
        self.title = title
        """**Заголовок темы**"""
        self.prefix = prefix
        """**Префикс темы**"""
        self.text_content = text_content
        """**Текст из темы**"""
        self.html_content = html_content
        """**Сырой контент темы**"""
        self.pages_count = pages_content
        """**Количество страниц с ответами в теме**"""
        self.is_closed = is_closed
        """**Закрыта ли тема**"""
        self.thread_post_id = thread_post_id
        """**ID сообщения темы (post_id)**"""
        self.url = f"{MAIN_URL}/threads/{self.id}/"
        """Ссылка на объект"""
    

    async def answer(self, message_html: str) -> aiohttp.ClientResponse:
        """Оставить сообщение в теме

        Attributes:
            message_html (str): Cодержание ответа. Рекомендуется использование HTML
        
        Returns:
            Объект Response модуля requests
        """

        return await self.API.answer_thread(self.id, message_html)


    async def watch(self, email_subscribe: bool = False, stop: bool = False) -> aiohttp.ClientResponse:
        """Изменить статус отслеживания темы

        Attributes:
            email_subscribe (bool): Отправлять ли уведомления на почту. По умолчанию False (необяз.)
            stop (bool): - Принудительно прекратить отслеживание. По умолчанию False (необяз.)
        
        Returns:
            Объект Response модуля requests
        """

        return await self.API.watch_thread(self.id, email_subscribe, stop)
    

    async def delete(self, reason: str, hard_delete: bool = False) -> aiohttp.ClientResponse:
        """Удалить тему

        Attributes:
            reason (str): Причина для удаления
            hard_delete (bool): Полное удаление сообщения. По умолчанию False (необяз.)
            
        Returns:
            Объект Response модуля requests
        """

        return await self.API.delete_thread(self.id, reason, hard_delete)
    

    async def edit(self, message_html: str) -> aiohttp.ClientResponse:
        """Отредактировать содержимое темы

        Attributes:
            message_html (str): Новое содержимое ответа. Рекомендуется использование HTML
        
        Returns:
            Объект Response модуля requests
        """

        return await self.API.edit_thread(self.id, message_html)

    async def edit_info(self, title: str = None, prefix_id: int = None, sticky: bool = True, opened: bool = True) -> aiohttp.ClientResponse:
        """Изменить заголовок и/или префикс темы

        Attributes:
            title (str): Новое название
            prefix_id (int): Новый ID префикса
            sticky (bool): Закрепить (True - закреп / False - не закреп)
            opened (bool): Открыть/закрыть тему (True - открыть / False - закрыть)
        
        Returns:
            Объект Response модуля requests
        """

        return await self.API.edit_thread_info(self.id, title, prefix_id, sticky, opened)
    

    async def get_posts(self, page: int = 1) -> list:
        """Получить все ID сообщений из темы на странице

        Attributes:
            page (int): Cтраница для поиска. По умолчанию 1 (необяз.)
        
        Returns:
            Список (list), состоящий из ID всех сообщений на странице
        """

        return await self.API.get_thread_posts(self.id, page)


    async def react(self, reaction_id: int = 1) -> aiohttp.ClientResponse:
        """Поставить реакцию на тему

        Attributes:
            reaction_id (int): ID реакции. По умолчанию 1 (необяз.)
            
        Returns:
            Объект Response модуля requests
        """

        return await self.API.react_thread(self.id, reaction_id)
    

    async def get_category(self) -> 'Category':
        """Получить родительский раздел раздела
        
        Returns:
            Объект Catrgory, в котором создан раздел
        """

        return await self.API.get_thread_category(self.id)