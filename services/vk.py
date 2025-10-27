import os
import time
import json

from vk_api import vk_api

from extensions.logging_ext import log
from extensions.path_ext import get_path
from services.tg_bot import TelegramAgent


class VKManager:
    """Взаимодействие с API"""

    def __init__(self, token:str, browser_manager):
        self.token = token
        self.browser_manager = browser_manager


    def get_friends_list(self, user_id:str):
        """Возвращает список друзей пользователя"""
        
        response = self._api_request('friends.get', user_id=user_id, fields='nickname')
        current_friends = {str(f['id']): f'{f['first_name']} {f['last_name']}' for f in response['items']}
        log.info(f'Список друзей получен: {len(current_friends)} чел.')
        self._save_friends_list_to_file(current_friends)
        return current_friends


    def _save_friends_list_to_file(self, current_friends: dict):
            """
            Сохраняет список друзей в файл, если файл существует - сравнивает список,
            если есть разница - высылает уведомление в ТГ.
            """

            FRIENDS_FILE_PATH = get_path('data', 'friends.json')
            tg = TelegramAgent()
            log.info('Проверка изменений в списке друзей...')
            
            if os.path.exists(FRIENDS_FILE_PATH):
                with open(FRIENDS_FILE_PATH, "r", encoding="utf-8") as f:
                    old_friends = json.load(f)      
                log.info(f"Загружен старый список друзей: {len(old_friends)} записей") 
            else:
                old_friends = {}
                log.info("Старый список друзей не найден, создаём новый")

            # Поиск пропавших и новых друзей
            lost_friends = set(old_friends) - set(current_friends)
            new_friends = set(current_friends) - set(old_friends)

            message_parts = []

            if lost_friends:
                lost_text = "\n".join(f"{uid}: {old_friends[uid]}" for uid in lost_friends)
                message_parts.append(f"Пропавшие друзья:\n{lost_text}")

            if new_friends:
                new_text = "\n".join(f"{uid}: {current_friends[uid]}" for uid in new_friends)
                message_parts.append(f"Новые друзья:\n{new_text}")

            if message_parts:
                message = "\n\n".join(message_parts)
                log.info("Обнаружены изменения, отправляю список в Telegram...")
                tg.send_message(message)
            else:
                log.info("Изменений в списке друзей не найдено.")

            # Сохраняем актуальный список друзей
            with open(FRIENDS_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(current_friends, f, ensure_ascii=False, indent=4)


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
    """Взаимодействие с браузером нацеленные на получение токена VK"""
    
    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
        self.KEY_PATTERN = ':web_token:login:auth'


    def get_vk_actual_access_token(self):
        """
        Запускает браузер, попытается получить токен с сайта,
        если авторизация не активна - перезапустит браузер в видимом режиме,
        будет ожидать авторизацию, как получит токен закроет браузер и вернёт токен.
        Если авторизация активна - вернёт токен.
        """

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