# Импортируем необходимые модули из FastAPI и SQLAlchemy
from fastapi import FastAPI, HTTPException, Request, Response
from sqlalchemy import and_, select, delete
# Импортируем uvicorn для запуска ASGI-приложения
import uvicorn
# Импортируем зависимости для работы с базой данных
from app.database import SessionDep, engine
# Импортируем middleware для обработки CORS-запросов
from fastapi.middleware.cors import CORSMiddleware
# Импортируем модели и схемы пользователей
from app.users.models import *
from app.users.schemas import *
# Импортируем настройки безопасности и конфигурацию AuthX
from app.auth import security, config
# Импортируем модуль requests для выполнения HTTP-запросов
import requests
# Импортируем модуль re для работы с регулярными выражениями (для проверки ссылок)
import re # Для проверки ссылок
# Импортируем GoogleTranslator для перевода текста
from deep_translator import GoogleTranslator # Для перевода
# Импортируем модуль random для генерации случайных чисел
import random

# Создаем экземпляр FastAPI приложения
app = FastAPI()

# Список разрешенных источников (origins) для CORS
origins = [
    "http://127.0.0.1:5500", # Разрешаем запросы с этого адреса
    "http://localhost:5500", # Разрешаем запросы с этого адреса
    "https://magical-cascaron-00274b.netlify.app",
    "https://booklamp.onrender.com/"

]

# Добавляем middleware для CORS
app.add_middleware(
    CORSMiddleware, # Используем CORSMiddleware
    allow_origins=origins, # Указываем разрешенные источники
    allow_credentials=True, # Разрешаем передачу учетных данных (например, cookie)
    allow_methods=["*"], # Разрешаем все HTTP-методы
    allow_headers=["*"], # Разрешаем все HTTP-заголовки
)

# Асинхронная функция для получения токена из cookie запроса
async def get_token_cookie(request: Request):
        # Получаем значение cookie с именем "my_access_token"
        token = request.cookies.get("my_access_token")
        # Если токен отсутствует, вызываем исключение HTTPException
        if not token:
            raise HTTPException(status_code=401, detail=f"Отсутствует токен")
        # Возвращаем токен
        return token

# Асинхронная функция для декодирования токена
async def decode_token(request: Request):
        # Получаем токен из cookie
        token = await get_token_cookie(request)
        # Декодируем токен с помощью метода _decode_token из AuthX
        payload = security._decode_token(token)
        # Извлекаем идентификатор пользователя (sub) из полезной нагрузки токена
        user_id = payload.decode(token, "super_puper_secret_key")
        # Возвращаем идентификатор пользователя
        return user_id.sub

# Декоратор события, которое выполняется при запуске приложения
@app.on_event("startup")
async def startup_event():
    # Асинхронный контекстный менеджер для работы с соединением к БД
    async with engine.begin() as conn:
        # Выполняем синхронную операцию создания всех таблиц в БД, определенных в Base.metadata
        await conn.run_sync(Base.metadata.create_all)

# Эндпоинт для регистрации нового пользователя (метод POST)
@app.post("/register")
async def register_user(data: UserRegisterSchema, session: SessionDep, response: Response):
        # Формируем запрос для проверки, существует ли пользователь с таким логином
        existing_user_query = select(UserModel).where(UserModel.login == data.login)
        # Выполняем запрос к базе данных
        existing_user_result = await session.execute(existing_user_query)
        # Если пользователь с таким логином найден, вызываем исключение
        if existing_user_result.scalars().first():
            raise HTTPException(status_code=409, detail="Такой пользователь существует")

        # Создаем новый экземпляр модели пользователя
        new_user = UserModel(
            login=data.login, # Устанавливаем логин
            password=data.password, # Устанавливаем пароль (в открытом виде, без хеширования)
            role=data.role # Устанавливаем роль пользователя
        )
        # Добавляем нового пользователя в сессию SQLAlchemy
        session.add(new_user)

        try:
            # Применяем изменения к базе данных, чтобы получить ID нового пользователя
            await session.flush()
            # Обновляем объект new_user данными из БД (включая ID и другие поля, которые могли быть установлены БД)
            await session.refresh(new_user)
        except Exception as e:
            # В случае ошибки откатываем транзакцию
            await session.rollback()
            # Вызываем исключение HTTPException с информацией об ошибке
            raise HTTPException(status_code=500, detail=f"Ошибка при сохранении пользователя в базе данных: {str(e)}")

        # Проверяем, был ли присвоен ID новому пользователю
        if new_user.id is None:
            # Если ID не присвоен, откатываем транзакцию
            await session.rollback()
            # Вызываем исключение HTTPException
            raise HTTPException(status_code=500, detail="Не удалось получить ID нового пользователя после сохранения.")

        # Создаем JWT токен доступа для нового пользователя, используя его ID
        token = security.create_access_token(uid=str(new_user.id))
        # Устанавливаем токен в cookie ответа
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, value=token, httponly=True, secure=True, samesite="none", path="/")
        # Подтверждаем транзакцию в базе данных
        await session.commit()
        # Возвращаем успешный ответ
        return {"ok": True}

# Эндпоинт для входа пользователя (метод POST)
@app.post("/login")
async def login_user(data: UserLoginSchema, session: SessionDep, response: Response):
        # Формируем запрос для поиска пользователя по логину и паролю
        query = select(UserModel).where(
            and_( # Используем оператор AND для объединения условий
                UserModel.login == data.login, # Проверяем совпадение логина
                UserModel.password == data.password # Проверяем совпадение пароля
            )
        )
        # Выполняем запрос к базе данных
        result = await session.execute(query)
        # Получаем первого найденного пользователя или None, если пользователь не найден
        user = result.scalars().first()

        # Если пользователь не найден, вызываем исключение HTTPException
        if user is None:
            raise HTTPException(status_code=401, detail="Неправильный логин или пароль")

        # Создаем JWT токен доступа для пользователя
        token = security.create_access_token(uid=str(user.id))
        # Устанавливаем токен в cookie ответа
        response.set_cookie(
            key=config.JWT_ACCESS_COOKIE_NAME, # Имя cookie
            value=token, # Значение токена
            httponly=True, # Флаг, делающий cookie недоступным для JavaScript на клиенте
            secure=True, # Флаг, указывающий, что cookie должен передаваться только по HTTPS
            samesite="none", # Атрибут SameSite для межсайтовых запросов (требует Secure=True)
            path="/", # Путь, для которого действителен cookie
        )
        # Возвращаем токен доступа в теле ответа
        return {"access_token": token}

# Эндпоинт для выхода пользователя (метод POST)
@app.post("/logout")
async def logout_user(response: Response):
    # Удаляем cookie с токеном доступа
    response.delete_cookie(config.JWT_ACCESS_COOKIE_NAME)
    # Возвращаем успешный ответ
    return {"ok": True}

# Эндпоинт для получения списка всех пользователей (метод GET)
@app.get("/get_all_users/")
async def get_users(session: SessionDep):
    # Формируем запрос для выбора всех записей из таблицы UserModel
    query = select(UserModel)
    # Выполняем запрос к базе данных
    result = await session.execute(query)
    # Возвращаем все найденные записи пользователей
    return result.scalars().all()

# Эндпоинт для удаления пользователя по ID (метод DELETE)
@app.delete("/user/{user_id}")
async def delete_user(user_id: int, session: SessionDep):
        # Формируем запрос для выбора пользователя по его ID
        query = select(UserModel).where(UserModel.id == user_id)
        # Выполняем запрос к базе данных
        result = await session.execute(query)
        # Получаем пользователя или None, если он не найден
        user = result.scalars().first()
    
        # Если пользователь не найден, вызываем исключение HTTPException
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
    
        # Удаляем пользователя из сессии SQLAlchemy
        await session.delete(user)
        # Подтверждаем транзакцию в базе данных
        await session.commit()
        # Возвращаем успешный ответ
        return {"ok": True}

# Эндпоинт для добавления книги в избранное (метод POST)
@app.post("/add_favorite")
async def add_favorite(
    book: BookBaseSchema, # Данные книги для добавления, валидируются схемой BookBaseSchema
    session: SessionDep, # Зависимость для получения сессии базы данных
    request: Request # Объект запроса для доступа к cookie
):
    # Декодируем токен из cookie, чтобы получить ID пользователя
    user_id_from_token = await decode_token(request) #Наша фунция которую создали выше
    
    # Создаем новый экземпляр модели FavoriteBook
    new_favorite = FavoriteBook(
        # decode_token возвращает ID, который можно преобразовать в int
        user_id=int(user_id_from_token), # Устанавливаем ID пользователя
        book_title=book.title, # Устанавливаем название книги
        book_author=book.author, # Устанавливаем автора книги
        book_genre=book.genre, # Устанавливаем жанр книги
        book_img_link=book.img_link, # Устанавливаем ссылку на изображение обложки
        book_url=book.url # Устанавливаем URL книги
    )
    # Добавляем новую запись в сессию SQLAlchemy
    session.add(new_favorite)
    # Подтверждаем транзакцию в базе данных
    await session.commit()
    # Возвращаем успешный ответ
    return {"ok": True}

# Эндпоинт для добавления книги в прочитанное (метод POST)
@app.post("/add_read")
async def add_read(
    book: BookBaseSchema, # Данные книги для добавления, валидируются схемой BookBaseSchema
    session: SessionDep, # Зависимость для получения сессии базы данных
    request: Request # Объект запроса для доступа к cookie
):
    # Декодируем токен из cookie, чтобы получить ID пользователя
    user_id_from_token = await decode_token(request)
    
    # Создаем новый экземпляр модели ReadBook
    new_read = ReadBook(
        user_id=int(user_id_from_token), # Устанавливаем ID пользователя
        book_title=book.title, # Устанавливаем название книги
        book_author=book.author, # Устанавливаем автора книги
        book_genre=book.genre, # Устанавливаем жанр книги
        book_img_link=book.img_link, # Устанавливаем ссылку на изображение обложки
        book_url=book.url # Устанавливаем URL книги
    )
    # Добавляем новую запись в сессию SQLAlchemy
    session.add(new_read)
    # Подтверждаем транзакцию в базе данных
    await session.commit()
    # Возвращаем успешный ответ
    return {"ok": True}

# Эндпоинт для получения списка избранных книг пользователя (метод GET)
@app.get("/get_favorites")
async def get_favorites(session: SessionDep, request: Request):
    # Декодируем токен из cookie, чтобы получить ID пользователя
    user_id_from_token = await decode_token(request)
    # Формируем запрос для выбора всех избранных книг текущего пользователя
    query = select(FavoriteBook).where(FavoriteBook.user_id == int(user_id_from_token))
    # Выполняем запрос к базе данных
    result = await session.execute(query)
    # Возвращаем все найденные избранные книги
    return result.scalars().all()

# Эндпоинт для получения списка прочитанных книг пользователя (метод GET)
@app.get("/get_read")
async def get_read(session: SessionDep, request: Request):
    # Декодируем токен из cookie, чтобы получить ID пользователя
    user_id_from_token = await decode_token(request)
    # Формируем запрос для выбора всех прочитанных книг текущего пользователя
    query = select(ReadBook).where(ReadBook.user_id == int(user_id_from_token))
    # Выполняем запрос к базе данных
    result = await session.execute(query)
    # Возвращаем все найденные прочитанные книги
    return result.scalars().all()

# Эндпоинт для удаления книги из избранного по ее ID (метод DELETE)
@app.delete("/remove_favorite/{item_id}")
async def remove_favorite(item_id: int, session: SessionDep, request: Request):
    # Декодируем токен из cookie, чтобы получить ID пользователя
    user_id_from_token = await decode_token(request)

    # Формируем запрос для выбора книги из избранного по ее ID и ID пользователя
    query = select(FavoriteBook).where(
        and_( # Используем оператор AND для объединения условий
            FavoriteBook.id == item_id, # Проверяем совпадение ID книги
            FavoriteBook.user_id == int(user_id_from_token) # Проверяем, что книга принадлежит текущему пользователю
        )
    )
    # Выполняем запрос к базе данных
    result = await session.execute(query)
    # Получаем книгу для удаления или None, если она не найдена
    book_to_delete = result.scalars().first()

    # Если книга не найдена, вызываем исключение HTTPException
    if book_to_delete is None:
        raise HTTPException(status_code=404, detail="Книга не найдена в избранном или не принадлежит вам.")

    # Удаляем книгу из сессии SQLAlchemy
    await session.delete(book_to_delete)
    # Подтверждаем транзакцию в базе данных
    await session.commit()
    # Возвращаем успешный ответ с сообщением
    return {"ok": True, "message": "Книга удалена из избранного."}

# Эндпоинт для удаления книги из прочитанного по ее ID (метод DELETE)
@app.delete("/remove_read/{item_id}")
async def remove_read(item_id: int, session: SessionDep, request: Request):
    # Декодируем токен из cookie, чтобы получить ID пользователя
    user_id_from_token = await decode_token(request)

    # Формируем запрос для выбора книги из прочитанного по ее ID и ID пользователя
    query = select(ReadBook).where(
        and_( # Используем оператор AND для объединения условий
            ReadBook.id == item_id, # Проверяем совпадение ID книги
            ReadBook.user_id == int(user_id_from_token) # Проверяем, что книга принадлежит текущему пользователю
        )
    )
    # Выполняем запрос к базе данных
    result = await session.execute(query)
    # Получаем книгу для удаления или None, если она не найдена
    book_to_delete = result.scalars().first()

    # Если книга не найдена, вызываем исключение HTTPException
    if book_to_delete is None:
        raise HTTPException(status_code=404, detail="Книга не найдена в прочитанном или не принадлежит вам.")

    # Удаляем книгу из сессии SQLAlchemy
    await session.delete(book_to_delete)
    # Подтверждаем транзакцию в базе данных
    await session.commit()
    # Возвращаем успешный ответ с сообщением
    return {"ok": True, "message": "Книга удалена из прочитанного."}

# Словарь для перевода основных жанров с русского на английский
GENRE_TRANSLATIONS = {
    "фантастика": "science_fiction",
    "фэнтези": "fantasy",
    "роман": "romance",
    "детектив": "mystery",
    "ужасы": "horror",
    "триллер": "thriller",
    "биография": "biography",
    "история": "history",
    "наука": "science",
    "поэзия": "poetry",
    "драма": "drama",
    "комедия": "comedy",
    "приключения": "adventure",
    "детские": "children",}

# Функция для перевода русского названия жанра в английский аналог
def translate_genre(russian_genre: str) -> str:
    # Приводим жанр к нижнему регистру и удаляем пробелы по краям
    lower_genre = russian_genre.lower().strip()
    # Возвращаем перевод из словаря или сам жанр, если перевод не найден
    return GENRE_TRANSLATIONS.get(lower_genre, lower_genre)

# Вспомогательная функция для перевода текста на русский язык
def translate_to_russian(text: str) -> str:
    # Если текст пустой, состоит из пробелов или является стандартной заглушкой, возвращаем его без изменений
    if not text or text.strip() == "" or text in ["Описание отсутствует", "Без названия", "Неизвестен"]:
        return text
    try:
        # Если текст уже содержит много русских букв (более половины символов), считаем его русским и не переводим
        if len(re.findall(r'[а-яА-Я]', text)) > len(text) / 2:
            return text
        # Используем GoogleTranslator для перевода с английского на русский
        return GoogleTranslator(source='en', target='ru').translate(text) or text # Возвращаем переведенный текст или оригинал, если перевод не удался
    except Exception as e:
        # В случае ошибки перевода выводим сообщение в консоль
        print(f"Ошибка перевода для текста '{text[:50]}...': {e}")
        # Возвращаем оригинальный текст в случае ошибки
        return text

# Асинхронная функция для получения описания книги по ее ключу с Open Library
async def get_book_description(book_key: str) -> str:
    try:
        # Выполняем GET-запрос к API Open Library для получения данных о книге
        response = requests.get(f"https://openlibrary.org{book_key}.json")
        # Проверяем, успешен ли запрос (статус код 2xx)
        response.raise_for_status()
        # Парсим JSON-ответ
        book_data = response.json()
        
        # Получаем описание книги из данных
        description = book_data.get("description")
        
        # Если описание представлено в виде словаря, извлекаем значение из поля "value"
        if isinstance(description, dict):
            return description.get("value", "Описание отсутствует")
        # Если описание является строкой, возвращаем его
        elif isinstance(description, str):
            return description
        # В остальных случаях возвращаем "Описание отсутствует"
        else:
            return "Описание отсутствует"
            
    except Exception:
        # В случае любой ошибки при получении или обработке описания возвращаем "Не удалось загрузить описание"
        return "Не удалось загрузить описание"

# Эндпоинт для получения случайной книги из API Open Library по заданному жанру (метод GET)
@app.get("/random_book")
async def get_random_russian_book(genre: str): # Принимает жанр на русском языке
    # Переводим русский жанр в английский для запроса к API
    english_genre = translate_genre(genre)
    
    try:
        # Генерируем случайное число (offset) от 0 до 2000 для получения разных книг
        random_offset = random.randint(0, 2000)
        
        # Формируем URL для запроса к Open Library, запрашиваем одну книгу со случайным offset
        url = f"https://openlibrary.org/subjects/{english_genre}.json?limit=1&offset={random_offset}"
        # Выполняем GET-запрос
        response = requests.get(url)
        # Проверяем, успешен ли запрос
        response.raise_for_status()
        
        # Извлекаем список работ (книг) из JSON-ответа
        books = response.json().get("works", [])
        
        # Если список книг пуст, вызываем исключение HTTPException
        if not books:
            raise HTTPException(
                status_code=404,
                detail=f"Книг в жанре '{genre}' не найдено"
            )
        
        # Берем единственную книгу из результата (т.к. limit=1)
        book = books[0]
        
        # Формируем URL для получения детальной информации о книге
        details_url = f"https://openlibrary.org{book['key']}.json"
        # Выполняем GET-запрос для получения деталей
        details = requests.get(details_url).json()
        # Получаем "сырое" описание книги из деталей
        raw_book_description = details.get("description")

        # Внутренняя функция для форматирования (сокращения) описания
        def format_description(desc):
            # Если описание отсутствует, возвращаем заглушку
            if not desc:
                return "Описание отсутствует"
            # Если описание представлено словарем, извлекаем значение из "value"
            if isinstance(desc, dict):
                desc = desc.get("value", "")
            
            # Ограничиваем описание: до первой точки, если слов больше 20
            words = desc.split() # Разбиваем описание на слова
            if len(words) <= 20: # Если слов 20 или меньше, возвращаем описание как есть
                return desc
            
            # Ищем первую точку после 20-го слова
            for i in range(20, len(words)):
                if words[i].endswith('.'): # Если слово заканчивается на точку
                    return ' '.join(words[:i+1]) # Возвращаем часть описания до этой точки включительно
            return desc # Если точка не найдена после 20 слов, возвращаем полное описание (или то, что было передано)

        # Инициализируем текст текущего описания заглушкой
        current_description_text = "Описание отсутствует"
        # Если "сырое" описание - это словарь, извлекаем значение
        if isinstance(raw_book_description, dict):
            current_description_text = raw_book_description.get("value", "Описание отсутствует")
        # Если "сырое" описание - это строка, используем ее
        elif isinstance(raw_book_description, str):
            current_description_text = raw_book_description

        # Форматируем (сокращаем) полученное описание
        formatted_description = format_description(current_description_text)

        # Проверяем НАЛИЧИЕ ССЫЛОК на openlibrary.org в УЖЕ ОТФОРМАТИРОВАННОМ описании
        # Если описание не является заглушкой и содержит ссылку на openlibrary.org, то заменяем его на "Описание отсутствует"
        if formatted_description != "Описание отсутствует" and re.search(r"https?://openlibrary\.org", formatted_description, re.IGNORECASE):
            final_description_for_translation = "Описание отсутствует"
        else:
            # В противном случае используем отформатированное описание для перевода
            final_description_for_translation = formatted_description

        # Формируем и возвращаем словарь с информацией о книге
        return {
            "title": translate_to_russian(book.get("title", "Без названия")), # Переводим название на русский
            "author": translate_to_russian(book.get("authors", [{}])[0].get("name", "Неизвестен")), # Переводим имя автора на русский
            "description": translate_to_russian(final_description_for_translation), # Переводим финальное описание на русский
            "imgLink": ( # Формируем ссылку на обложку книги
                f"https://covers.openlibrary.org/b/id/{book['cover_id']}-L.jpg" # Используем cover_id, если он есть
                if "cover_id" in book else None # Иначе ссылка будет None
            ),
            "genre": genre, # Возвращаем оригинальный русский жанр, который был в запросе
            "url": f"https://openlibrary.org{book['key']}" # URL книги на Open Library
        }
        
    except requests.exceptions.RequestException as e: # Обрабатываем ошибки, связанные с HTTP-запросами
        raise HTTPException( # Вызываем исключение HTTPException
            status_code=502, # Статус код "Bad Gateway"
            detail=f"Ошибка при запросе к Open Library: {str(e)}" # Сообщение об ошибке
        )


# Этот блок выполняется, если скрипт запускается напрямую (а не импортируется как модуль)
if __name__ == "__main__":
    # Запускаем ASGI-сервер uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0") # Указываем путь к приложению FastAPI и хост
