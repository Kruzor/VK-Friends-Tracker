import json
import urllib.parse
import urllib.request

from extensions.logging_ext import log
from extensions.dotenv_ext import get_env


class TelegramAgent:
    """Отправка сообщений через Telegram Bot API без сторонних библиотек"""

    def __init__(self):
        self.BOT_TOKEN = get_env('TG_BOT_TOKEN')
        self.CHAT_ID = get_env('TG_CHAT_ID')

    def send_message(self, text: str):
        """Отправляет сообщение в Telegram"""

        url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": self.CHAT_ID,
            "text": text
        }
        encoded_data = urllib.parse.urlencode(data).encode()

        try:
            with urllib.request.urlopen(url, data=encoded_data) as response:
                result = json.loads(response.read())
                if result.get('ok'):
                    log.info(f'Сообщение отправлено в Telegram (chat_id={self.CHAT_ID})')
                else:
                    log.error(f'Ошибка API Telegram: {result}')
        except Exception as e:
            log.error(f'Непредвиденная ошибка при отправке сообщения в Telegram: {e}')