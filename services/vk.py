import time

from vk_api import vk_api

from extensions.logging_ext import log
from extensions.dotenv_ext import get_env
from extensions.path_ext import get_path
from services.browser import BrowserManager


class VKManager:

    def __init__(self, token:str, browser_manager):
        self.token = token
        self.browser_manager = browser_manager


    def get_friends_list(self, user_id:str):
        """Возвращает список друзей пользователя"""
        
        return self._api_request('friends.get', user_id=user_id, fields='nickname')


    def _api_request(self, api_method: str, **params):
        """
        Выполняет запрос к VK API по названию метода.
        Пример: api_request('users.get', user_ids=1)
        Возвращает dict, при ошибке вернёт None.
        """
        try:
            vk_session = vk_api.VkApi(token=self.token)
            vk = vk_session.get_api()
            parts = api_method.split('.')
            method = vk
            for part in parts:
                method = getattr(method, part)

            response = method(**params)
            return response

        except Exception as e:
            log.error(f'Ошибка при выполнении {api_method}: {e}')
            return None
        

class VKInteraction:
    
    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
        self.KEY_PATTERN = ':web_token:login:auth'

    def get_vk_actual_access_token(self):
        self.browser_manager.start_browser()
        page = self._open_vk_url()
        if page == 'vkuiPanel__in':
            log.info('Требуется авторизация на сайте, перезапускаю браузер в обычном режиме')
            self.browser_manager.start_browser(headless = False)
            self._open_vk_url()
            log.info('Ожидание авторизации на сайте, после авторизации браузер закроется в течении минуты...')

            while True:
                token = self.browser_manager.get_token(self.KEY_PATTERN)
                if token:
                    self.browser_manager.stop_browser()
                    return token
                time.sleep(60)

        elif page == 'vkitTextClamp__root--8Ttiw':
            log.info('Авторизация на сайте активна')
            token = self.browser_manager.get_token(self.KEY_PATTERN)
            self.browser_manager.stop_browser()
            return token


    def _open_vk_url(self) -> str:
        """
        Открывает сайт VK, 
        если откроется страница авторизации - вернёт один класс,
        если лента - другой.
        """
        vk_url = 'https://vk.com'
        class_in_unauthorized_page = 'vkuiPanel__in'
        class_in_authorized_page = 'vkitTextClamp__root--8Ttiw'
        self.browser_manager.open_url(vk_url)
        which_class = self.browser_manager.wait_page_load(class_in_unauthorized_page, class_in_authorized_page)
        return which_class