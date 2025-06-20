# Импортируем BaseModel из Pydantic для создания моделей данных (схем)
from pydantic import BaseModel
# Импортируем Optional из typing для указания необязательных полей
from typing import Optional

# Определяем схему данных для регистрации пользователя, наследуясь от BaseModel
class UserRegisterSchema(BaseModel):
    # Поле login: строка, обязательное для заполнения
    login: str
    # Поле password: строка, обязательное для заполнения
    password: str
    # Поле role: строка, по умолчанию имеет значение "User"
    role: str = "User"

# Определяем схему данных для входа пользователя, наследуясь от BaseModel
class UserLoginSchema(BaseModel):
    # Поле login: строка, обязательное для заполнения
    login: str
    # Поле password: строка, обязательное для заполнения
    password: str

# Определяем базовую схему данных для книги, наследуясь от BaseModel
class BookBaseSchema(BaseModel):
    # Поле title: строка, название книги, обязательное для заполнения
    title: str
    # Поле author: строка, автор книги, обязательное для заполнения
    author: str
    # Поле genre: строка, жанр книги, обязательное для заполнения
    genre: str
    # Поле img_link: строка, ссылка на изображение обложки, необязательное (Optional), по умолчанию None
    img_link: Optional[str] = None
    # Поле url: строка, URL книги, обязательное для заполнения
    url: str
