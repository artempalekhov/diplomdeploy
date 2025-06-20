# Импортируем BaseSettings из pydantic_settings для создания класса настроек,
# который может считывать переменные окружения и имеет значения по умолчанию.
from pydantic_settings import BaseSettings
# Импортируем DeclarativeBase из SQLAlchemy ORM для создания базового класса
# для всех моделей базы данных.
from sqlalchemy.orm import DeclarativeBase

# Определяем класс Settings, наследуемый от BaseSettings.
# Этот класс будет содержать все настройки приложения.
class Settings(BaseSettings):
    # Определяем переменную DATABASE_URL с типом str.
    # Это URL для подключения к базе данных.
    # По умолчанию используется асинхронная SQLite база данных 'books.db' в текущей директории.
    DATABASE_URL: str = "sqlite+aiosqlite:///./books.db"

# Создаем экземпляр класса Settings.
# Этот объект 'settings' будет использоваться в других частях приложения для доступа к настройкам.
settings = Settings()

# Определяем класс Base, наследуемый от DeclarativeBase.
# Все модели SQLAlchemy (таблицы базы данных) в приложении будут наследоваться от этого класса.
class Base(DeclarativeBase):
    # pass здесь означает, что класс не добавляет никакой новой функциональности
    # к DeclarativeBase, но служит как центральная точка для всех моделей.
    pass
