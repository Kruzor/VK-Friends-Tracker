import sys
import time
import threading

from extensions.logging_ext import log
from extensions.dotenv_ext import get_env
from services.browser import BrowserManager
from services.vk import VKManager, VKInteraction
from services.gui import start_gui


REFRESH_INTERVAL = int(get_env('REFRESH_INTERVAL'))
USER_ID = get_env('USER_ID')

browser_manager = BrowserManager()
app, gui_window = start_gui(browser_manager)
log.info("GUI запущен")


def main_function_decorator():
    """
    Декоратор главной функции, в случае возникновения непредвиденной ошибки
    или прерывания кода действиями пользователя - закрывает процесс браузера
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                log.info("Главный цикл запущен")
                return func(*args, **kwargs)
                
            except KeyboardInterrupt:
                log.info("Прервано пользователем.")
                browser_manager.stop_browser()
            
            except PermissionError as e:
                log.error(f"Ошибка с ключом токена: {e}")
                return

            except Exception as e:
                log.error(f"Произошла непредвиденная ошибка: {e}")
                browser_manager.stop_browser()

        return wrapper
    return decorator


@main_function_decorator()
def main():
    while True:
        vk_interaction = VKInteraction(browser_manager)
        token = vk_interaction.get_vk_actual_access_token()
        vk_manager = VKManager(token, browser_manager)
        vk_manager.get_friends_list(USER_ID)
        log.warning(f"Ожидание перед следующим обновлением: {REFRESH_INTERVAL} сек.")
        time.sleep(REFRESH_INTERVAL)
        log.info("Инициализация нового цикла обновления...")
        log.info("")


if __name__ == '__main__':
    thread = threading.Thread(target=main, daemon=True)
    thread.start()
    sys.exit(app.exec())