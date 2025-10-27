import os

from dotenv import load_dotenv

from extensions.path_ext import get_path


load_dotenv(dotenv_path=get_path('data', 'settings.env'))

def get_env(env_name:str) -> str:
    """
    Возвращает строку с данными по названию из .env файлой,
    если данные не найдены - вернёт None.
    """
    return str(os.getenv(env_name, default=None))

__all__ = ['get_env']