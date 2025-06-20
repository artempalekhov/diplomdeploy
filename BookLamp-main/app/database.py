# Импортируем Annotated для аннотаций типов с дополнительной информацией
from typing import Annotated
# Импортируем Depends из FastAPI для внедрения зависимостей
from fastapi import Depends
# Импортируем необходимые компоненты из SQLAlchemy для асинхронной работы с базой данных
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# Импортируем настройки (settings) из конфигурационного файла приложения
from app.config import settings

# Создаем асинхронный "движок" (engine) для подключения к базе данных
engine = create_async_engine(
    url=settings.DATABASE_URL # URL для подключения к базе данных берется из настроек
)

# Создаем фабрику асинхронных сессий (async_sessionmaker)
# Эта фабрика будет использоваться для создания новых сессий для взаимодействия с БД
# expire_on_commit=False означает, что объекты SQLAlchemy не будут автоматически "просрочены" (detached) после коммита транзакции,
# что позволяет продолжать использовать их атрибуты без необходимости нового запроса к БД.
new_session = async_sessionmaker(engine, expire_on_commit=False)

# Асинхронная функция-генератор для получения сессии базы данных
async def get_session():
    # Асинхронный контекстный менеджер для работы с сессией
    # Сессия автоматически открывается и закрывается при входе и выходе из блока with
    async with new_session() as session:
        # yield передает управление (и сессию) в зависимую функцию (например, в эндпоинт FastAPI)
        # После того как зависимая функция завершит свою работу, выполнение вернется сюда
        yield session

# Создаем аннотированный тип SessionDep для внедрения зависимости сессии в эндпоинты FastAPI
# Annotated[AsyncSession, Depends(get_session)] означает, что параметр, аннотированный как SessionDep,
# будет иметь тип AsyncSession, и его значение будет предоставлено функцией get_session.
SessionDep = Annotated[AsyncSession, Depends(get_session)]
