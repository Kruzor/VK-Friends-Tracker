import os


BASE_DIR = os.getcwd()

def get_path(*paths:str) -> str:
    """
    Возвращает путь к файлу/папке, 
    начало пути - директория запуска.
    """
    return str(os.path.join(BASE_DIR, *paths))

__all__ = ["get_path"]