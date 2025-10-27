import os
import re
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import SessionNotCreatedException
from webdriver_manager.chrome import ChromeDriverManager

from extensions.logging_ext import log
from extensions.path_ext import get_path


class BrowserManager:
    """Управление браузером"""
    
    def __init__(self):
        self.PROFILE_NAME = 'script'
        self.PROFILE_DIR = get_path('data', 'profile_data')
        
        # Связь функций управления для одного экземпляра класса
        self.driver = None


    def start_browser(self, headless:bool | None = True):
        """
        Запускает экземпляр браузера с отдельным профилем, 
        если указать headless False - запустится обычном режиме,
        по умолчанию headless - True. Возвращает driver.
        Если есть зависший процесс браузера с аналогичным профилем - 
        будет доталово пытаться его закрыть и запустить новый.
        Если есть уже запущенный экземпляр браузера - закроет его.
        При возникновении непредвиденной ошибки - вернёт None.
        """

        try:
            if self.driver:
                self.stop_browser()
                return self.start_browser()
            
            log.info('Попытка запуска браузера...')
            options = Options()
            options.add_argument(f'--profile-directory={self.PROFILE_NAME}')
            options.add_argument(f'--user-data-dir={self.PROFILE_DIR}')
            if headless:
                log.info("Запуск браузера в headless режиме")
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--window-size=900,600')
        
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            log.info('Браузер успешно запущен')
            return self.driver
        
        except SessionNotCreatedException:
            log.error('Chrome не удалось создать сессию, пробуем закрыть зависший процесс...')
            os.system('taskkill /f /im chrome.exe')
            log.info('Повторная попытка')
            return self.start_browser()

        except Exception as e:
            log.error(f'Произошла непредвиденная ошибка: {e}')
            return None
        

    def stop_browser(self):
            """Останавливает процесс браузера"""

            log.info("Попытка остановить браузер...")
            if self.driver is not None:
                self.driver.quit()
                self.driver = None
                log.info("Браузер успешно остановлен")
            else:
                log.info("Браузер не был запущен")


    def open_url(self, url: str):
        """Открывает переданную страницу в браузере"""

        if self.driver:
            log.info(f"Открываем URL: {url}")
            self.driver.get(url)
        else:
            log.warning("Невозможно открыть URL: браузер не запущен")


    def get_token(self, key_pattern:str) -> str:
        """
        Возвращает токен, ищет по регулярному выражению,
        если не найден - возвращает None.
        """
        
        data = self._get_data_from_localstorage()
        if data is not None:
            token = self._parse_token(key_pattern, data)
            return token
        else:
            return None


    def wait_page_load(self, class1:str, class2:str) -> str:
        """
        Ожидает загрузки страницы, ждёт пока один из двух классов не появится.
        Рассчитано что один класс с страницы авторизации, второй с главной страницы.
        Возвращает название класса который был обнаружен, если не обнаружен - None. 
        """

        log.info('Ожидаем загрузки страницы...')

        WebDriverWait(self.driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CLASS_NAME, class1)),
                EC.presence_of_element_located((By.CLASS_NAME, class2))
            )
        )

        if self.driver.find_elements(By.CLASS_NAME, class1):
            log.info(f'Страница загружена. Найден класс - {class1}')
            return class1
        
        elif self.driver.find_elements(By.CLASS_NAME, class2):
            log.info(f'Страница загружена. Найден класс - {class2}')
            return class2
        else:
            log.error('Ни один из классов не найден')
            return None


    def _get_data_from_localstorage(self):
        """
        Получаем все данные key - value из localStorage браузера.
        Возвращает данные со значениями или None.
        """

        js = """
        var out = {};
        try {
            for (var i = 0; i < localStorage.length; i++) {
                var k = localStorage.key(i);
                out[k] = localStorage.getItem(k);
            }
        } catch (e) {
            return {'_error': String(e)};
        }
        return out;
        """
        
        try:
            data = self.driver.execute_script(js)
            log.info("LocalStorage успешно прочитан")
        
        except Exception as e:
            log.error(f"Ошибка при чтении localStorage: {e}")
            return None
        
        if not isinstance(data, dict):
            log.error(f'Неожиданный localStorage дамп: {data}')
            return None
        
        if '_error' in data:
            log.error(f"Ошибка JS при чтении localStorage: {data['_error']}")
            return None
        
        return data
    

    def _parse_token(self, key_pattern:str, data:dict) -> str:
        """
        Попытаться извлечь token из полученных данных localStorage,
        возвращает токен или None. Ищет по регулярному выражению.
        """
        
        log.info("Начинаем поиск токена в localStorage...")
        # Ищем ключи по шаблону
        matched = [(key, value) for key, value in data.items() if key_pattern in key or re.search(key_pattern, key)]
        if not matched:
            log.warning(f"Ключ с шаблоном {key_pattern} не найден")
            token = None
        else:
            # Берём последний элемент (предположительно самый новый)
            _, value = matched[-1]

            # Парсим JSON и достаём token
            try:
                value_json = json.loads(value)
                token = value_json.get('access_token')
                if token:
                    log.info("Access_token найден")
                else:
                    log.warning("Access_token не найден в JSON")

                return token
            
            except json.JSONDecodeError:
                log.warning("Не удалось распарсить значение ключа JSON")
                token = None