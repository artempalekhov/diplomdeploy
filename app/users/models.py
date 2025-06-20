# Импортируем Annotated для создания аннотаций типов с дополнительной информацией и List для указания типа списка
from typing import Annotated, List
# Импортируем Mapped и mapped_column для декларативного определения колонок таблицы,
# а также relationship для определения связей между таблицами из SQLAlchemy ORM
from sqlalchemy.orm import Mapped, mapped_column, relationship
# Импортируем ForeignKey для определения внешних ключей из SQLAlchemy
from sqlalchemy import ForeignKey
# Импортируем базовый класс Base из конфигурационного файла приложения, от которого наследуются все модели
from app.config import Base

# Создаем аннотированный тип intpk для первичного ключа типа integer
# mapped_column(primary_key=True, autoincrement=True) указывает, что это первичный ключ и он автоинкрементируемый
intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]

# Определяем модель пользователя, наследуясь от базового класса Base
class UserModel(Base):
    # Указываем имя таблицы в базе данных
    __tablename__ = "Users"

    # Определяем колонку id как первичный ключ типа intpk (int, primary_key, autoincrement)
    id: Mapped[intpk]
    # Определяем колонку login как строку (varchar)
    login: Mapped[str]
    # Определяем колонку password как строку (varchar)
    password: Mapped[str]
    # Определяем колонку role как строку (varchar)
    role: Mapped[str]
    # Определяем связь "один-ко-многим" с моделью FavoriteBook
    # favorites будет списком объектов FavoriteBook, связанных с этим пользователем
    # back_populates="user" указывает на атрибут 'user' в модели FavoriteBook, который является обратной связью
    favorites: Mapped[List["FavoriteBook"]] = relationship(back_populates="user")
    # Определяем связь "один-ко-многим" с моделью ReadBook
    # read_books будет списком объектов ReadBook, связанных с этим пользователем
    # back_populates="user" указывает на атрибут 'user' в модели ReadBook, который является обратной связью
    read_books: Mapped[List["ReadBook"]] = relationship(back_populates="user")

# Определяем модель для избранных книг, наследуясь от базового класса Base
class FavoriteBook(Base):
    # Указываем имя таблицы в базе данных
    __tablename__ = "favorite_books"
    
    # Определяем колонку id как первичный ключ типа intpk
    id: Mapped[intpk]
    # Определяем колонку user_id как внешний ключ, ссылающийся на колонку id таблицы "Users"
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"))
    # Определяем колонку book_title как строку (varchar) для хранения названия книги
    book_title: Mapped[str]
    # Определяем колонку book_author как строку (varchar) для хранения автора книги
    book_author: Mapped[str]
    # Определяем колонку book_genre как строку (varchar) для хранения жанра книги
    book_genre: Mapped[str]
    # Определяем колонку book_img_link как строку (varchar), которая может быть NULL (nullable=True), для хранения ссылки на изображение обложки
    book_img_link: Mapped[str] = mapped_column(nullable=True)
    # Определяем колонку book_url как строку (varchar) для хранения URL книги
    book_url: Mapped[str]
    
    # Определяем связь "многие-к-одному" с моделью UserModel
    # user будет объектом UserModel, которому принадлежит эта запись в избранном
    # back_populates="favorites" указывает на атрибут 'favorites' в модели UserModel, который является обратной связью
    user: Mapped["UserModel"] = relationship(back_populates="favorites")

# Определяем модель для прочитанных книг, наследуясь от базового класса Base
class ReadBook(Base):
    # Указываем имя таблицы в базе данных
    __tablename__ = "read_books"
    
    # Определяем колонку id как первичный ключ типа intpk
    id: Mapped[intpk]
    # Определяем колонку user_id как внешний ключ, ссылающийся на колонку id таблицы "Users"
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"))
    # Определяем колонку book_title как строку (varchar) для хранения названия книги
    book_title: Mapped[str]
    # Определяем колонку book_author как строку (varchar) для хранения автора книги
    book_author: Mapped[str]
    # Определяем колонку book_genre как строку (varchar) для хранения жанра книги
    book_genre: Mapped[str]
    # Определяем колонку book_img_link как строку (varchar), которая может быть NULL (nullable=True), для хранения ссылки на изображение обложки
    book_img_link: Mapped[str] = mapped_column(nullable=True)
    # Определяем колонку book_url как строку (varchar) для хранения URL книги
    book_url: Mapped[str]
    
    # Определяем связь "многие-к-одному" с моделью UserModel
    # user будет объектом UserModel, которому принадлежит эта запись в прочитанных книгах
    # back_populates="read_books" указывает на атрибут 'read_books' в модели UserModel, который является обратной связью
    user: Mapped["UserModel"] = relationship(back_populates="read_books")
