import aiohttp
from typing import TYPE_CHECKING
from arizona_forum_async.consts import MAIN_URL

if TYPE_CHECKING:
    from arizona_forum_async import ArizonaAPI


class Category:
    def __init__(self, API: 'ArizonaAPI', id: int, title: str, pages_count: int) -> None:
        self.API = API
        self.id = id
        """**ID категории**"""
        self.title = title
        """**Название категории**"""
        self.pages_count = pages_count
        """**Количество страниц в категории**"""
        self.url = f"{MAIN_URL}/forums/{self.id}/"
        """Ссылка на объект"""

    async def create_thread(self, title: str, message_html: str, discussion_type: str = 'discussion', watch_thread: int = 1) -> aiohttp.ClientResponse:
        """Создать тему в категории

        Attributes:
            title (str): Название темы
            message_html (str): Содержание темы. Рекомендуется использование HTML
            discussion_type (str): - Тип темы | Возможные варианты: 'discussion' - обсуждение (по умолчанию), 'article' - статья, 'poll' - опрос (необяз.)
            watch_thread (str): - Отслеживать ли тему. По умолчанию True (необяз.)
        
        Returns:
            Объект Response модуля requests

        Todo:
            Cделать возврат ID новой темы
        """

        return await self.API.create_thread(self.id, title, message_html, discussion_type, watch_thread)
    

    async def get_parent_category(self) -> 'Category':
        """Получить родительский раздел

        Attributes:
            thread_id (int): ID темы
        
        Returns:
            Объект Catrgory, в котормо создана тема
        """

        return await self.API.get_parent_category_of_category(self.id)


    async def set_read(self) -> aiohttp.ClientResponse:
        """Отметить категорию как прочитанную
        
        Returns:
            Объект Response модуля requests
        """

        return await self.API.set_read_category(self.id)
    

    async def watch(self, notify: str, send_alert: bool = True, send_email: bool = False, stop: bool = False) -> aiohttp.ClientResponse:
        """Настроить отслеживание категории

        Attributes:
            notify (str): Объект отслеживания. Возможные варианты: "thread", "message", ""
            send_alert (bool): - Отправлять ли уведомления на форуме. По умолчанию True (необяз.)
            send_email (bool): - Отправлять ли уведомления на почту. По умолчанию False (необяз.)
            stop (bool): - Принудительное завершение отслеживания. По умолчанию False (необяз.)

        Returns:
            Объект Response модуля requests    
        """

        return await self.API.watch_category(self.id, notify, send_alert, send_email, stop)
    

    async def get_threads(self, page: int = 1) -> dict:
        """Получить темы из раздела

        Attributes:
            page (int): Cтраница для поиска. По умолчанию 1 (необяз.)
            
        Returns:
            Словарь (dict), состоящий из списков закрепленных ('pins') и незакрепленных ('unpins') тем
        """

        return await self.API.get_threads(self.id, page)
    
    async def get_threads_extended(self, page: int = 1) -> dict:
        """Получить темы из раздела с дополнительной информацией

        Attributes:
            page (int): Cтраница для поиска. По умолчанию 1 (необяз.)
            
        Returns:
            Словарь (dict), состоящий из списков закрепленных ('pins') и незакрепленных ('unpins') тем
        """

        return await self.API.get_threads_extended(self.id, page)


    async def get_categories(self) -> list:
        """Получить дочерние категории из раздела
        
        Returns:
            Список (list), состоящий из ID дочерних категорий раздела
        """

        return await self.API.get_categories(self.id)
