import aiohttp
from bs4 import BeautifulSoup
from re import compile, findall
import re
from html import unescape
from typing import List, Dict, Optional, Union

from arizona_forum_async.consts import MAIN_URL, ROLE_COLOR
from arizona_forum_async.bypass_antibot import bypass_async

from arizona_forum_async.exceptions import IncorrectLoginData, ThisIsYouError
from arizona_forum_async.models.other import Statistic
from arizona_forum_async.models.post_object import Post, ProfilePost
from arizona_forum_async.models.member_object import Member, CurrentMember
from arizona_forum_async.models.thread_object import Thread
from arizona_forum_async.models.category_object import Category


class ArizonaAPI:
    def __init__(self, user_agent: str, cookie: dict) -> None:
        self.user_agent = user_agent
        self.cookie_str = "; ".join([f"{k}={v}" for k, v in cookie.items()])
        self._session: aiohttp.ClientSession = None
        self._token: str = None

    
    async def connect(self, do_bypass: bool = True):
        """Асинхронный метод для создания сессии, получения токена и обхода анти-бота."""
        if self._session is None or self._session.closed:
            cookies = {}
            for item in self.cookie_str.split('; '):
                name, value = item.strip().split('=', 1)
                cookies[name] = value

            if do_bypass:
                bypass_cookie_str, _ = await bypass_async(self.user_agent)
                name, value = bypass_cookie_str.split('=', 1)
                cookies[name] = value

            self._session = aiohttp.ClientSession(
                headers={"user-agent": self.user_agent},
                cookies=cookies
            )

            try:
                async with self._session.get(f"{MAIN_URL}/account/") as response:
                    response.raise_for_status()
                    html_content_main = await response.text()
                    soup_main = BeautifulSoup(html_content_main, 'lxml')
                    html_tag = soup_main.find('html')
                    if not html_tag or html_tag.get('data-logged-in') == "false":
                        raise IncorrectLoginData("Неверные cookie или сессия истекла.")

                async with self._session.get(f"{MAIN_URL}/help/terms/") as response:
                    response.raise_for_status()
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'lxml')
                    self._token = soup.find('html')['data-csrf']
                    if not self._token:
                        raise Exception("Не удалось получить CSRF токен.")

            except (aiohttp.ClientError, IncorrectLoginData, Exception) as e:
                if self._session:
                    await self._session.close()
                self._session = None
                raise Exception(f"Ошибка подключения или авторизации: {e}") from e

    async def close(self):
        """Асинхронный метод для закрытия сессии."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    @property
    async def token(self) -> str:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        if not self._token:
            async with self._session.get(f"{MAIN_URL}/help/terms/") as response:
                response.raise_for_status()
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'lxml')
                self._token = soup.find('html')['data-csrf']
        return self._token

    async def get_current_member(self) -> CurrentMember:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        try:
            async with self._session.get(f"{MAIN_URL}/account/") as response:
                response.raise_for_status()
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'lxml')
                avatar_span = soup.find('span', {'class': 'avatar--xxs'})
                if not avatar_span or not avatar_span.has_attr('data-user-id'):
                    raise Exception("Не удалось найти ID текущего пользователя на странице аккаунта.")
                user_id = int(avatar_span['data-user-id'])

            member_info = await self.get_member(user_id)
            if not member_info:
                raise Exception(f"Не удалось получить информацию для пользователя с ID {user_id}")

            return CurrentMember(self, user_id, member_info.username, member_info.user_title,
                                member_info.avatar, member_info.roles, member_info.messages_count,
                                member_info.reactions_count, member_info.trophies_count, member_info.username_color)
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении данных текущего пользователя: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении данных текущего пользователя: {e}")
            return None

    async def get_category(self, category_id: int) -> 'Category | None':
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/forums/{category_id}"
        params = {'_xfResponseType': 'json', '_xfToken': token}
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get('status') == 'error':
                    return None

                html_content = unescape(data['html']['content'])
                soup = BeautifulSoup(html_content, 'lxml')
                title = unescape(data['html']['title'])
                try:
                    pages_count = int(soup.find_all('li', {'class': 'pageNav-page'})[-1].text)
                except (IndexError, AttributeError, ValueError):
                    pages_count = 1

                return Category(self, category_id, title, pages_count)
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении категории {category_id}: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении категории {category_id}: {e}")
            return None


    async def get_member(self, user_id: int) -> 'Member | None':
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/members/{user_id}"
        params = {'_xfResponseType': 'json', '_xfToken': token}
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get('status') == 'error':
                    return None

                html_content = unescape(data['html']['content'])
                soup = BeautifulSoup(html_content, 'lxml')
                username = unescape(data['html']['title'])

                username_class = soup.find('span', class_='username')
                username_color = '#fff'
                if username_class:
                    for style in ROLE_COLOR:
                        if style in str(username_class):
                            username_color = ROLE_COLOR[style]
                            break

                roles = []
                roles_container = soup.find('div', {'class': 'memberHeader-banners'})
                if roles_container:
                    for i in roles_container.children:
                        if i.text != '\n': roles.append(i.text.strip()) # Added strip()

                try:
                    user_title_tag = soup.find('span', {'class': 'userTitle'})
                    user_title = user_title_tag.text if user_title_tag else None
                except AttributeError:
                    user_title = None

                try:
                    avatar_tag = soup.find('a', {'class': 'avatar avatar--l'})
                    avatar = MAIN_URL + avatar_tag['href'] if avatar_tag and avatar_tag.has_attr('href') else None
                except TypeError:
                    avatar = None

                messages_count = 0
                reactions_count = 0
                trophies_count = 0

                try:
                    msg_tag = soup.find('a', {'href': f'/search/member?user_id={user_id}'})
                    if msg_tag: messages_count = int(msg_tag.text.strip().replace(',', ''))
                except (AttributeError, ValueError): pass

                try:
                    react_tag = soup.find('dl', {'class': 'pairs pairs--rows pairs--rows--centered'})
                    if react_tag:
                        dd_tag = react_tag.find('dd')
                        if dd_tag: reactions_count = int(dd_tag.text.strip().replace(',', ''))
                except (AttributeError, ValueError): pass

                try:
                    trophy_tag = soup.find('a', {'href': f'/members/{user_id}/trophies'})
                    if trophy_tag: trophies_count = int(trophy_tag.text.strip().replace(',', ''))
                except (AttributeError, ValueError): pass

                return Member(self, user_id, username, user_title, avatar, roles, messages_count, reactions_count, trophies_count, username_color)

        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении пользователя {user_id}: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении пользователя {user_id}: {e}")
            return None


    async def get_thread(self, thread_id: int) -> 'Thread | None':
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/threads/{thread_id}/page-1"
        params = {'_xfResponseType': 'json', '_xfToken': token}
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get('status') == 'error':
                    return None

                if data.get('redirect'):
                    try:
                        redirect_path = data['redirect'].strip(MAIN_URL)
                        new_thread_id = int(redirect_path.split('/')[1].split('-')[-1])
                        return await self.get_thread(new_thread_id)
                    except (IndexError, ValueError):
                        print(f"Не удалось извлечь thread_id из редиректа: {data['redirect']}")
                        return None

                html_content = unescape(data['html']['content'])
                content_h1_html = unescape(data['html']['h1'])
                content_soup = BeautifulSoup(html_content, 'lxml')
                content_h1_soup = BeautifulSoup(content_h1_html, 'lxml')

                creator = None
                creator_tag = content_soup.find('a', {'class': 'username'})
                if creator_tag and creator_tag.has_attr('data-user-id'):
                    creator_id = int(creator_tag['data-user-id'])
                    try:
                        creator = await self.get_member(creator_id)
                    except Exception as e:
                        print(f"Ошибка получения создателя ({creator_id}) для темы {thread_id}: {e}")
                    if not creator:
                        creator = Member(self, creator_id, creator_tag.text, None, None, None, None, None, None, None)
                else:
                    print(f"Не удалось найти информацию о создателе для темы {thread_id}")
                    return None


                create_date_tag = content_soup.find('time')
                create_date = int(create_date_tag['data-time']) if create_date_tag and create_date_tag.has_attr('data-time') else 0

                prefix_tag = content_h1_soup.find('span', {'class': 'label'})
                if prefix_tag:
                    prefix = prefix_tag.text
                    title = content_h1_soup.text.strip(prefix).strip()
                else:
                    prefix = ""
                    title = content_h1_soup.text.strip()

                thread_html_content_tag = content_soup.find('div', {'class': 'bbWrapper'})
                thread_html_content = str(thread_html_content_tag) if thread_html_content_tag else ""
                thread_content = thread_html_content_tag.text if thread_html_content_tag else ""

                try:
                    pages_count = int(content_soup.find_all('li', {'class': 'pageNav-page'})[-1].text)
                except (IndexError, AttributeError, ValueError):
                    pages_count = 1

                is_closed = bool(content_soup.find('dl', {'class': 'blockStatus'}))

                post_article_tag = content_soup.find('article', {'id': compile(r'js-post-\d+')})
                thread_post_id = int(post_article_tag['id'].strip('js-post-')) if post_article_tag and post_article_tag.has_attr('id') else 0

                return Thread(self, thread_id, creator, create_date, title, prefix, thread_content, thread_html_content, pages_count, thread_post_id, is_closed)

        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении темы {thread_id}: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении темы {thread_id}: {e}")
            return None


    async def get_post(self, post_id: int) -> 'Post | None':
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        url = f"{MAIN_URL}/posts/{post_id}"
        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                html_content = await response.text()

            content_soup = BeautifulSoup(html_content, 'lxml')
            post_article = content_soup.find('article', {'id': f'js-post-{post_id}'})
            if post_article is None:
                return None

            creator = None
            creator_info_tag = post_article.find('a', {'data-xf-init': 'member-tooltip'})
            if creator_info_tag and creator_info_tag.has_attr('data-user-id'):
                creator_id = int(creator_info_tag['data-user-id'])
                try:
                    creator = await self.get_member(creator_id)
                except Exception as e:
                    print(f"Ошибка получения создателя ({creator_id}) для поста {post_id}: {e}")
                if not creator:
                    creator = Member(self, creator_id, creator_info_tag.text, None, None, None, None, None, None, None)
            else:
                print(f"Не удалось найти информацию о создателе для поста {post_id}")
                return None

            thread = None
            html_tag = content_soup.find('html')
            if html_tag and html_tag.has_attr('data-content-key') and html_tag['data-content-key'].startswith('thread-'):
                try:
                    thread_id = int(html_tag['data-content-key'].strip('thread-'))
                    thread = await self.get_thread(thread_id)
                except (ValueError, Exception) as e:
                    print(f"Ошибка получения темы для поста {post_id}: {e}")
            if not thread:
                print(f"Не удалось получить информацию о теме для поста {post_id}")
                return None

            create_date_tag = post_article.find('time', {'class': 'u-dt'})
            create_date = int(create_date_tag['data-time']) if create_date_tag and create_date_tag.has_attr('data-time') else 0

            html_content_tag = post_article.find('div', {'class': 'bbWrapper'})
            html_content = str(html_content_tag) if html_content_tag else ""
            text_content = html_content_tag.text if html_content_tag else ""

            return Post(self, post_id, creator, thread, create_date, html_content, text_content)

        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении поста {post_id}: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении поста {post_id}: {e}")
            return None


    async def get_profile_post(self, post_id: int) -> 'ProfilePost | None':
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        url = f"{MAIN_URL}/profile-posts/{post_id}"
        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                html_content = await response.text()

            content_soup = BeautifulSoup(html_content, 'lxml')
            post_article = content_soup.find('article', {'id': f'js-profilePost-{post_id}'})
            if post_article is None:
                return None

            creator = None
            creator_tag = post_article.find('a', {'class': 'username'})
            if creator_tag and creator_tag.has_attr('data-user-id'):
                creator_id = int(creator_tag['data-user-id'])
                creator = await self.get_member(creator_id)
                if not creator:
                    print(f"Не удалось получить создателя ({creator_id}) для поста профиля {post_id}")
                    return None
            else:
                print(f"Не удалось найти ID создателя для поста профиля {post_id}")
                return None

            profile_owner = None
            profile_owner_tag = post_article.find('h4', {'class': 'attribution'})
            if profile_owner_tag:
                profile_link = profile_owner_tag.find('a', {'class': 'username'})
                if profile_link and profile_link.has_attr('data-user-id'):
                    try:
                        profile_id = int(profile_link['data-user-id'])
                        profile_owner = await self.get_member(profile_id)
                    except (ValueError, Exception) as e:
                        print(f"Ошибка получения владельца профиля ({profile_id}) для поста {post_id}: {e}")

            if not profile_owner:
                print(f"Не удалось определить владельца профиля для поста {post_id}")
                return None

            create_date_tag = post_article.find('time')
            create_date = int(create_date_tag['data-time']) if create_date_tag and create_date_tag.has_attr('data-time') else 0

            html_content_tag = post_article.find('div', {'class': 'bbWrapper'})
            html_content = str(html_content_tag) if html_content_tag else ""
            text_content = html_content_tag.text if html_content_tag else ""

            return ProfilePost(self, post_id, creator, profile_owner, create_date, html_content, text_content)

        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении поста профиля {post_id}: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении поста профиля {post_id}: {e}")
            return None

    async def get_forum_statistic(self) -> 'Statistic | None':
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        url = MAIN_URL
        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                html_content = await response.text()

            content_soup = BeautifulSoup(html_content, 'lxml')

            threads_count = 0
            posts_count = 0
            users_count = 0
            last_register_member = None

            try:
                threads_tag = content_soup.find('dl', {'class': 'pairs pairs--justified count--threads'})
                if threads_tag:
                    dd_tag = threads_tag.find('dd')
                    if dd_tag: threads_count = int(dd_tag.text.replace(',', ''))
            except (AttributeError, ValueError): pass

            try:
                posts_tag = content_soup.find('dl', {'class': 'pairs pairs--justified count--messages'})
                if posts_tag:
                    dd_tag = posts_tag.find('dd')
                    if dd_tag: posts_count = int(dd_tag.text.replace(',', ''))
            except (AttributeError, ValueError): pass

            try:
                users_tag = content_soup.find('dl', {'class': 'pairs pairs--justified count--users'})
                if users_tag:
                    dd_tag = users_tag.find('dd')
                    if dd_tag: users_count = int(dd_tag.text.replace(',', ''))
            except (AttributeError, ValueError): pass

            try:
                latest_member_dl = content_soup.find('dl', {'class': 'pairs pairs--justified'})
                if latest_member_dl:
                    latest_member_link = latest_member_dl.find('a', {'data-user-id': True})
                    if latest_member_link and latest_member_link.has_attr('data-user-id'):
                        last_user_id = int(latest_member_link['data-user-id'])
                        last_register_member = await self.get_member(last_user_id)
            except (AttributeError, ValueError, Exception) as e:
                print(f"Ошибка получения последнего зарегистрированного пользователя: {e}")


            return Statistic(self, threads_count, posts_count, users_count, last_register_member)

        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении статистики форума: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении статистики форума: {e}")
            return None
    

        # ---------------================ МЕТОДЫ ОБЪЕКТОВ ====================--------------------

    # CATEGORY
    async def create_thread(self, category_id: int, title: str, message_html: str, discussion_type: str = 'discussion', watch_thread: bool = True) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/forums/{category_id}/post-thread"
        params = {'inline-mode': '1'}
        payload = {
            '_xfToken': token,
            'title': title,
            'message_html': message_html,
            'discussion_type': discussion_type,
            'watch_thread': int(watch_thread)
        }
        try:
            response = await self._session.post(url, params=params, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при создании темы в категории {category_id}: {e}")
            raise e


    async def set_read_category(self, category_id: int) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/forums/{category_id}/mark-read"
        payload = {'_xfToken': token}
        try:
            response = await self._session.post(url, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при отметке категории {category_id} как прочитанной: {e}")
            raise e


    async def watch_category(self, category_id: int, notify: str, send_alert: bool = True, send_email: bool = False, stop: bool = False) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/forums/{category_id}/watch"
        if stop:
            payload = {'_xfToken': token, 'stop': "1"}
        else:
            payload = {
                '_xfToken': token,
                'send_alert': int(send_alert),
                'send_email': int(send_email),
                'notify': notify
            }
        try:
            response = await self._session.post(url, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при настройке отслеживания категории {category_id}: {e}")
            raise e


    async def get_threads(self, category_id: int, page: int = 1) -> Optional[Dict[str, List[int]]]:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/forums/{category_id}/page-{page}"
        params = {'_xfResponseType': 'json', '_xfToken': token}
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get('status') == 'error':
                    return None

                html_content = unescape(data['html']['content'])
                soup = BeautifulSoup(html_content, "lxml")
                result = {'pins': [], 'unpins': []}
                for thread in soup.find_all('div', compile('structItem structItem--thread.*')):
                    link_tags = thread.find_all('div', "structItem-title")[0].find_all("a")
                    if not link_tags: continue
                    link = link_tags[-1]
                    thread_ids = findall(r'\d+', link.get('href', ''))
                    if not thread_ids: continue

                    thread_id = int(thread_ids[0])
                    if len(thread.find_all('i', {'title': 'Закреплено'})) > 0:
                        result['pins'].append(thread_id)
                    else:
                        result['unpins'].append(thread_id)
                return result
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении тем из категории {category_id} (страница {page}): {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении тем из категории {category_id} (страница {page}): {e}")
            return None


    async def get_thread_category_detail(self, category_id: int, page: int = 1) -> Optional[List[Dict]]:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/forums/{category_id}/page-{page}"
        params = {'_xfResponseType': 'json', '_xfToken': token}
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get('status') == 'error':
                    return None

                html_content = unescape(data['html']['content'])
                soup = BeautifulSoup(html_content, "lxml")
                result = []
                seen_thread_ids = set()

                for thread in soup.find_all('div', class_=compile('structItem structItem--thread.*')):
                    title_div = thread.find('div', "structItem-title")
                    if not title_div: continue
                    link_tags = title_div.find_all("a")
                    if not link_tags: continue
                    link = link_tags[-1]

                    thread_ids = findall(r'\d+', link.get('href', ''))
                    if not thread_ids: continue
                    thread_id = int(thread_ids[0])

                    if thread_id in seen_thread_ids:
                        continue
                    seen_thread_ids.add(thread_id)

                    thread_data = {}

                    minor_div = thread.find('div', 'structItem-cell--main').find('div', 'structItem-minor')
                    username_author_tag = minor_div.find('ul', 'structItem-parts').find('a', class_='username') if minor_div else None
                    thread_data['username_author'] = username_author_tag.text.strip() if username_author_tag else None
                    thread_data['thread_title'] = link.text.strip()

                    prefix_label = title_div.find('span', class_='label')
                    thread_data['prefix'] = prefix_label.text.strip() if prefix_label else None

                    thread_data['username_author_color'] = '#fff'
                    if username_author_tag:
                        for style, color in ROLE_COLOR.items():
                            if style in str(username_author_tag):
                                thread_data['username_author_color'] = color
                                break

                    start_date_li = minor_div.find('li', 'structItem-startDate') if minor_div else None
                    time_tag = start_date_li.find('time', class_='u-dt') if start_date_li else None
                    created_date = time_tag.get('data-time') if time_tag else None
                    thread_data['created_date'] = int(created_date) if created_date and created_date.isdigit() else None

                    latest_cell = thread.find('div', 'structItem-cell--latest')
                    last_message_username_tag = latest_cell.find('div', 'structItem-minor').find(class_=compile('username')) if latest_cell else None
                    thread_data['username_last_message'] = last_message_username_tag.text.strip() if last_message_username_tag else None

                    thread_data['username_last_message_color'] = '#fff'
                    if last_message_username_tag:
                         for style, color in ROLE_COLOR.items():
                            if style in str(last_message_username_tag):
                                thread_data['username_last_message_color'] = color
                                break

                    latest_date_tag = latest_cell.find('time', class_='structItem-latestDate') if latest_cell else None
                    last_message_date = latest_date_tag.get('data-time') if latest_date_tag else None
                    thread_data['last_message_date'] = int(last_message_date) if last_message_date and last_message_date.isdigit() else None

                    thread_data['thread_id'] = thread_id
                    thread_data['is_pinned'] = len(thread.find_all('i', {'title': 'Закреплено'})) > 0
                    thread_data['is_closed'] = len(thread.find_all('i', {'title': 'Закрыта'})) > 0

                    result.append(thread_data)

                return result
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении расширенных тем из категории {category_id} (страница {page}): {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении расширенных тем из категории {category_id} (страница {page}): {e}")
            return None


    async def get_parent_category_of_category(self, category_id: int) -> Optional[Category]:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        url = f"{MAIN_URL}/forums/{category_id}"
        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'lxml')

                breadcrumbs = soup.find('ul', {'class': 'p-breadcrumbs'})
                if not breadcrumbs: return None
                parent_li = breadcrumbs.find_all('li')
                if len(parent_li) < 2: return None
                parent_link = parent_li[-1].find('a')
                if not parent_link or not parent_link.get('href'): return None

                href_parts = parent_link['href'].split('/')
                if len(href_parts) < 3: return None
                parent_category_id_str = href_parts[2]

                if not parent_category_id_str.isdigit():
                    return None

                parent_category_id = int(parent_category_id_str)
                return await self.get_category(parent_category_id)
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении родительской категории для {category_id}: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении родительской категории для {category_id}: {e}")
            return None


    async def get_categories(self, category_id: int) -> Optional[List[int]]:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/forums/{category_id}/page-1" # page-1 может быть багом в оригинале?
        params = {'_xfResponseType': 'json', '_xfToken': token}
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get('status') == 'error':
                    return None

                html_content = unescape(data['html']['content'])
                soup = BeautifulSoup(html_content, "lxml")
                categories = []
                for category_div in soup.find_all('div', compile('.*node--depth2 node--forum.*')):
                    link = category_div.find("a")
                    if link and link.get('href'):
                         ids = findall(r'\d+', link['href'])
                         if ids:
                             categories.append(int(ids[0]))
                return categories
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении дочерних категорий из {category_id}: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении дочерних категорий из {category_id}: {e}")
            return None


    # MEMBER
    async def follow_member(self, member_id: int) -> aiohttp.ClientResponse:
        if member_id == self.current_member.id:
            raise ThisIsYouError(member_id)
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/members/{member_id}/follow"
        payload = {'_xfToken': token}
        try:
            response = await self._session.post(url, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при подписке/отписке от пользователя {member_id}: {e}")
            raise e


    async def ignore_member(self, member_id: int) -> aiohttp.ClientResponse:
        if member_id == self.current_member.id:
            raise ThisIsYouError(member_id)
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/members/{member_id}/ignore"
        payload = {'_xfToken': token}
        try:
            response = await self._session.post(url, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при игнорировании/отмене игнорирования пользователя {member_id}: {e}")
            raise e


    async def add_profile_message(self, member_id: int, message_html: str) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/members/{member_id}/post"
        payload = {'_xfToken': token, 'message_html': message_html}
        try:
            response = await self._session.post(url, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при добавлении сообщения на стену пользователя {member_id}: {e}")
            raise e


    async def get_profile_messages(self, member_id: int, page: int = 1) -> Optional[List[int]]:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/members/{member_id}/page-{page}"
        params = {'_xfResponseType': 'json', '_xfToken': token}
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get('status') == 'error':
                    return None

                html_content = unescape(data['html']['content'])
                soup = BeautifulSoup(html_content, "lxml")
                messages = []
                for post in soup.find_all('article', {'id': compile('js-profilePost-*')}):
                    post_id_str = post.get('id', '').strip('js-profilePost-')
                    if post_id_str.isdigit():
                         messages.append(int(post_id_str))
                return messages
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении сообщений профиля {member_id} (страница {page}): {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении сообщений профиля {member_id} (страница {page}): {e}")
            return None


    # POST
    async def react_post(self, post_id: int, reaction_id: int = 1) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f'{MAIN_URL}/posts/{post_id}/react'
        params = {'reaction_id': str(reaction_id)}
        payload = {'_xfToken': token}
        try:
            response = await self._session.post(url, params=params, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при установке реакции на пост {post_id}: {e}")
            raise e


    async def edit_post(self, post_id: int, message_html: str) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token

        post_info = await self.get_post(post_id)
        if not post_info or not post_info.thread:
            raise ValueError(f"Не удалось получить информацию о посте {post_id} для редактирования")
        else:
            title_of_thread_post = post_info.thread.title

        url = f"{MAIN_URL}/posts/{post_id}/edit"
        payload = {
            "_xfToken": token,
            "title": title_of_thread_post,
            "message_html": message_html,
            "message": message_html
        }
        try:
            response = await self._session.post(url, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при редактировании поста {post_id}: {e}")
            raise e


    async def delete_post(self, post_id: int, reason: str, hard_delete: bool = False) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/posts/{post_id}/delete"
        payload = {
            "_xfToken": token,
            "reason": reason,
            "hard_delete": int(hard_delete)
        }
        try:
            response = await self._session.post(url, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при удалении поста {post_id}: {e}")
            raise e

    async def bookmark_post(self, post_id: int) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/posts/{post_id}/bookmark"
        payload = {"_xfToken": token}
        try:
            response = await self._session.post(url, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при добавлении поста {post_id} в закладки: {e}")
            raise e

    # PROFILE POST
    async def react_profile_post(self, post_id: int, reaction_id: int = 1) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f'{MAIN_URL}/profile-posts/{post_id}/react'
        params = {'reaction_id': str(reaction_id)}
        payload = {'_xfToken': token}
        try:
            response = await self._session.post(url, params=params, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при установке реакции на пост профиля {post_id}: {e}")
            raise e


    async def comment_profile_post(self, post_id: int, message_html: str) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/profile-posts/{post_id}/add-comment"
        payload = {"_xfToken": token, "message_html": message_html}
        try:
            response = await self._session.post(url, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при комментировании поста профиля {post_id}: {e}")
            raise e


    async def delete_profile_post(self, post_id: int, reason: str, hard_delete: bool = False) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/profile-posts/{post_id}/delete"
        payload = {
            "_xfToken": token,
            "reason": reason,
            "hard_delete": int(hard_delete)
        }
        try:
            response = await self._session.post(url, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при удалении поста профиля {post_id}: {e}")
            raise e


    async def edit_profile_post(self, post_id: int, message_html: str) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/profile-posts/{post_id}/edit"
        payload = {
            "_xfToken": token,
            "message_html": message_html,
            "message": message_html
        }
        try:
            response = await self._session.post(url, data=payload)
            return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при редактировании поста профиля {post_id}: {e}")
            raise e

    async def answer_thread(self, thread_id: int, message_html: str) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/threads/{thread_id}/add-reply"
        payload = {
            '_xfToken': token,
            'message_html': message_html
        }
        try:
            async with self._session.post(url, data=payload) as response:
                return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при ответе в теме {thread_id}: {e}")
            raise e

    async def watch_thread(self, thread_id: int, email_subscribe: bool = False, stop: bool = False) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/threads/{thread_id}/watch"
        payload = {
            '_xfToken': token,
            'stop': int(stop),
            'email_subscribe': int(email_subscribe)
        }
        try:
            async with self._session.post(url, data=payload) as response:
                return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при изменении статуса отслеживания темы {thread_id}: {e}")
            raise e

    async def delete_thread(self, thread_id: int, reason: str, hard_delete: bool = False) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/threads/{thread_id}/delete"
        payload = {
            "reason": reason,
            "hard_delete": int(hard_delete),
            "_xfToken": token
        }
        try:
            async with self._session.post(url, data=payload) as response:
                return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при удалении темы {thread_id}: {e}")
            raise e

    async def edit_thread(self, thread_id: int, message_html: str) -> Optional[aiohttp.ClientResponse]:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        get_url = f"{MAIN_URL}/threads/{thread_id}/page-1"
        thread_post_id = None

        try:
            async with self._session.get(get_url) as response:
                response.raise_for_status()
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'lxml')
                post_article = soup.find('article', {'id': compile('js-post-*')})
                if post_article and 'id' in post_article.attrs:
                    thread_post_id = post_article['id'].strip('js-post-')
                else:
                    print(f"Не удалось найти ID первого поста для темы {thread_id}")
                    return None

        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении информации для редактирования темы {thread_id}: {e}")
            return None
        except Exception as e:
            print(f"Ошибка парсинга при получении информации для редактирования темы {thread_id}: {e}")
            return None

        if not thread_post_id:
             return None

        edit_url = f"{MAIN_URL}/posts/{thread_post_id}/edit"
        payload = {
            "message_html": message_html,
            "message": message_html,
            "_xfToken": token
        }
        try:
            async with self._session.post(edit_url, data=payload) as response:
                return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при редактировании темы {thread_id} (пост {thread_post_id}): {e}")
            raise e


    async def edit_thread_info(self, thread_id: int, title: str, prefix_id: Optional[int] = None, sticky: bool = True, opened: bool = True) -> aiohttp.ClientResponse:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/threads/{thread_id}/edit"
        payload = {
            "_xfToken": token,
            'title': title
        }

        if prefix_id is not None:
            payload['prefix_id'] = prefix_id
        if opened:
            payload["discussion_open"] = 1
        else:
            pass
        if sticky:
            payload["sticky"] = 1

        try:
            async with self._session.post(url, data=payload) as response:
                return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при изменении информации темы {thread_id}: {e}")
            raise e


    async def get_thread_category(self, thread_id: int) -> Optional['Category']:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")

        url = f"{MAIN_URL}/threads/{thread_id}/page-1"
        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'lxml')

                html_tag = soup.find('html')
                if not html_tag or 'data-container-key' not in html_tag.attrs:
                    print(f"Не удалось найти data-container-key для темы {thread_id}")
                    return None

                container_key = html_tag['data-container-key']
                if not container_key.startswith('node-'):
                     print(f"Некорректный data-container-key '{container_key}' для темы {thread_id}")
                     return None

                category_id_str = container_key.strip('node-')
                try:
                    category_id = int(category_id_str)
                except ValueError:
                    print(f"Не удалось преобразовать ID категории '{category_id_str}' в число для темы {thread_id}")
                    return None

                return await self.get_category(category_id)

        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении категории темы {thread_id}: {e}")
            return None
        except Exception as e:
            print(f"Ошибка парсинга при получении категории темы {thread_id}: {e}")
            return None

    async def get_thread_posts(self, thread_id: int, page: int = 1) -> Optional[List[str]]:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        url = f"{MAIN_URL}/threads/{thread_id}/page-{page}"
        params = {'_xfResponseType': 'json', '_xfToken': token}
        try:
            async with self._session.get(url, params=params) as response:
                if response.status == 404:
                    return []
                response.raise_for_status()
                data = await response.json()

                if data.get('status') == 'error':
                    return None

                if 'html' not in data or 'content' not in data['html']:
                    return []

                soup = BeautifulSoup(unescape(data['html']['content']), "lxml")
                posts = soup.find_all('article', {'id': compile('js-post-*')})
                return [i['id'].strip('js-post-') for i in posts if 'id' in i.attrs]

        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении постов темы {thread_id}, стр {page}: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении постов темы {thread_id}, стр {page}: {e}")
            return None

    async def get_all_thread_posts(self, thread_id: int) -> List[str]:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token

        all_posts_ids = []
        page = 1
        pages_count = 1
        processed_first_page = False

        while True:
            url = f"{MAIN_URL}/threads/{thread_id}/page-{page}"
            params = {'_xfResponseType': 'json', '_xfToken': token}
            try:
                async with self._session.get(url, params=params) as response:
                    if response.status == 404 and page > 1:
                         break
                    response.raise_for_status()
                    data = await response.json()

                    if data.get('status') == 'error':
                        if page == 1:
                            print(f"API вернуло ошибку на первой странице темы {thread_id}: {data.get('errors')}")
                        break

                    if 'html' not in data or 'content' not in data['html']:
                        print(f"Ответ API для темы {thread_id} стр {page} не содержит HTML.")
                        if page == 1:
                            return []
                        else:
                            break

                    html_content = unescape(data['html']['content'])
                    soup = BeautifulSoup(html_content, "lxml")
                    current_page_posts = soup.find_all('article', {'id': compile('js-post-*')})
                    post_ids = [i['id'].strip('js-post-') for i in current_page_posts if 'id' in i.attrs]

                    if not post_ids and page > 1:
                         break

                    all_posts_ids.extend(post_ids)

                    if not processed_first_page:
                        pages_count = 1
                        try:
                            page_nav = soup.find('ul', class_='pageNav-main')
                            if page_nav:
                                last_page_li = page_nav.find_all('li', class_='pageNav-page')
                                if last_page_li:
                                     pages_count = int(last_page_li[-1].text)
                        except (IndexError, AttributeError, ValueError, TypeError):
                             pages_count = 1
                        processed_first_page = True

                    if page >= pages_count:
                        break

                    page += 1

            except aiohttp.ClientError as e:
                print(f"Ошибка сети при получении всех постов темы {thread_id}, стр {page}: {e}")
                break
            except Exception as e:
                print(f"Неожиданная ошибка при получении всех постов темы {thread_id}, стр {page}: {e}")
                break

        return all_posts_ids


    async def react_thread(self, thread_id: int, reaction_id: int = 1) -> Optional[aiohttp.ClientResponse]:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        token = await self.token
        get_url = f"{MAIN_URL}/threads/{thread_id}/page-1"
        thread_post_id = None

        try:
            async with self._session.get(get_url) as response:
                response.raise_for_status()
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'lxml')
                post_article = soup.find('article', {'id': compile('js-post-*')})
                if post_article and 'id' in post_article.attrs:
                    thread_post_id = post_article['id'].strip('js-post-')
                else:
                    print(f"Не удалось найти ID первого поста для реакции в теме {thread_id}")
                    return None

        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении ID поста для реакции в теме {thread_id}: {e}")
            return None
        except Exception as e:
            print(f"Ошибка парсинга при получении ID поста для реакции в теме {thread_id}: {e}")
            return None

        if not thread_post_id:
            return None

        react_url = f'{MAIN_URL}/posts/{thread_post_id}/react'
        params = {'reaction_id': str(reaction_id)}
        payload = {'_xfToken': token}

        try:
            async with self._session.post(react_url, params=params, data=payload) as response:
                return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при установке реакции {reaction_id} на пост {thread_post_id} темы {thread_id}: {e}")
            raise e

    # OTHER
    async def send_form(self, form_id: int, data: dict) -> aiohttp.ClientResponse:
        """Заполнить форму

        Attributes:
            form_id (int): ID формы
            data (dict): Информация для запонения в виде словаря. Форма словаря: {'question[id вопроса]' = 'необходимая информация'} | Пример: {'question[531]' = '1'}
        
        Returns:
            Объект Response модуля aiohttp
        """
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        
        data.update({'_xfToken': await self.token})
        try:
            async with self._session.post(f"{MAIN_URL}/form/{form_id}/submit", data=data) as response:
                return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при отправке формы {form_id}: {e}")
            raise e

    async def get_notifications(self) -> list:
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        url = f"{MAIN_URL}/account/alerts"
        notifications = []
        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'lxml')

                for alert in soup.find_all('li', {'class': 'js-alert'}):
                    if not alert.has_attr('data-alert-id'):
                        continue

                    sender = None
                    username_link = alert.find('a', {'class': 'username'})
                    if username_link:
                        sender_id_str = username_link.get('data-user-id', '0')
                        sender = {
                            'id': int(sender_id_str) if sender_id_str.isdigit() else 0,
                            'name': unescape(username_link.get_text(strip=True)),
                            'avatar': None,
                            'avatar_color': None,
                            'initials': None
                        }

                        avatar_container = alert.find('div', class_='contentRow-figure')
                        if avatar_container:
                             avatar_img = avatar_container.find('img', {'class': 'avatar'})
                             avatar_span = avatar_container.find('span', {'class': 'avatar'})

                             if avatar_img and avatar_img.has_attr('src'):
                                 sender['avatar'] = avatar_img['src']
                             elif avatar_span and 'avatar--default' in avatar_span.get('class', []):
                                sender['avatar_color'] = avatar_span.get('style')
                                sender['initials'] = unescape(avatar_span.get_text(strip=True)) if avatar_span else None


                    time_tag = alert.find('time', {'class': 'u-dt'})
                    timestamp = None
                    if time_tag:
                        timestamp = {
                            'iso': time_tag.get('datetime'),
                            'unix': int(time_tag['data-time']) if time_tag and time_tag.has_attr('data-time') and time_tag['data-time'].isdigit() else None
                        }

                    alert_text_container = alert.find('div', {'class': 'contentRow-main'})
                    alert_text = unescape(alert_text_container.get_text(strip=True)) if alert_text_container else None

                    link_tag = alert.find('a', {'class': 'fauxBlockLink-blockLink'})
                    link = link_tag['href'] if link_tag and link_tag.has_attr('href') else None

                    alert_data = {
                        'id': alert.get('data-alert-id'),
                        'is_unread': 'is-unread' in alert.get('class', []),
                        'text': alert_text,
                        'link': f"{MAIN_URL}{link}" if link and link.startswith('/') else link,
                        'sender': sender,
                        'timestamp': timestamp
                    }

                    notifications.append(alert_data)

            return notifications
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при получении уведомлений: {e}")
            return []
        except Exception as e:
            print(f"Неожиданная ошибка при получении уведомлений: {e}")
            return []

    async def search_threads(self, query: str, sort: str = 'relevance') -> list:
        """Поиск тем по форуму с заданными параметрами
        
        Attributes:
            query (str): Поисковый запрос
            sort (str): Тип сортировки (relevance, date, etc)
            
        Returns:
            Список словарей с информацией о найденных темах
        """
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
            
        url = f"{MAIN_URL}/search/24587779/?q={query}&o={sort}"
        results = []
        
        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                html_content = await response.text()
                content = BeautifulSoup(html_content, 'lxml')
                
                for thread in content.find_all('li', {'class': 'block-row'}):
                    title_link = thread.find('h3', {'class': 'contentRow-title'}).find('a')
                    date_tag = thread.find('time', {'class': 'u-dt'})
                    answers_tag = thread.find(text=re.compile('Ответы: '))
                    
                    thread_data = {
                        'title': title_link.text.strip().split('| Причина:')[0].strip(),
                        'status': thread.find('span', {'class': 'label'}).text if thread.find('span', {'class': 'label'}) else None,
                        'author': thread['data-author'],
                        'thread_id': int(title_link['href'].split('/')[-2]),
                        'create_date': int(date_tag['data-time']) if date_tag else None,
                        'answers_count': int(answers_tag.split(': ')[1]) if answers_tag else 0,
                        'forum': thread.find('a', href=re.compile('/forums/')).text if thread.find('a', href=re.compile('/forums/')) else None,
                        'snippet': thread.find('div', {'class': 'contentRow-snippet'}).text.strip() if thread.find('div', {'class': 'contentRow-snippet'}) else None,
                        'url': f"{MAIN_URL}{title_link['href']}"
                    }
                    
                    results.append(thread_data)
                    
            return results
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при поиске тем по запросу '{query}': {e}")
            return []
        except Exception as e:
            print(f"Неожиданная ошибка при поиске тем '{query}': {e}")
            return []

    async def mark_notifications_read(self, alert_ids: list[int]) -> aiohttp.ClientResponse:
        """Пометить уведомления как прочитанные"""
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
            
        data = {
            '_xfToken': await self.token,
            'alert_id': alert_ids,
            '_xfAction': 'toggle',
            '_xfWithData': 1
        }
        
        try:
            async with self._session.post(
                f"{MAIN_URL}/account/alert-toggle",
                data=data
            ) as response:
                return response
        except aiohttp.ClientError as e:
            print(f"Ошибка сети при пометке уведомлений {alert_ids} как прочитанных: {e}")
            raise e

    async def get_post_bbcode(self, thread_id: int, post_id: int) -> str:
        """Получить BB-код поста по его ID.

        Сначала получает HTML-содержимое поста,
        затем отправляет этот HTML для конвертации в BBCode.

        Args:
            thread_id: ID темы, содержащей пост.
            post_id: ID поста для получения BB-кода.

        Returns:
            Строка с BB-кодом поста или пустая строка в случае ошибки.

        Raises:
            Exception: Если сессия не активна.
        """
        if not self._session or self._session.closed:
            raise Exception("Сессия не активна. Вызовите connect() сначала.")
        try:
            token = await self.token
        except Exception as e:
            print(f"Не удалось получить токен: {e}")
            return ''

        html_content = ''
        try:
            post = await self.get_post(post_id)
            html_content = post.html_content
        except aiohttp.ClientError as e:
            print(f"Сетевая ошибка при получении HTML для поста {post_id}: {e}")
        except Exception as e:
            print(f"Неожиданная ошибка при получении HTML для поста {post_id}: {e}")
        try:
            convert_url = f"{MAIN_URL}/index.php?editor/to-bb-code"
            data_post = {
                '_xfResponseType': 'json',
                '_xfRequestUri': f'/threads/{thread_id}/',
                '_xfWithData': 1,
                '_xfToken': token,
                'html': html_content
            }
            async with self._session.post(convert_url, data=data_post) as response:
                response.raise_for_status()
                convert_data = await response.json()
                if convert_data.get("status") == "ok" and "bbCode" in convert_data:
                    bbcode = convert_data.get('bbCode', '')
                    return unescape(bbcode)
                else:
                    print(f"Ошибка при конвертации BBCode для поста {post_id}. Ответ сервера: {convert_data}")
                    return ''

        except aiohttp.ClientError as e:
            print(f"Сетевая ошибка при конвертации BBCode для поста {post_id}: {e}")
            return ''
        except Exception as e:
            print(f"Неожиданная ошибка при конвертации BBCode для поста {post_id}: {e}")
            return ''