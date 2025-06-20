# Импортируем timedelta из модуля datetime для работы с интервалами времени,
# например, для установки времени жизни токена.
from datetime import timedelta
# Импортируем AuthX и AuthXConfig из библиотеки authx
# AuthXConfig используется для настройки параметров аутентификации,
# AuthX - основной класс для работы с аутентификацией.
from authx import AuthX, AuthXConfig

# Создаем экземпляр конфигурации AuthXConfig.
config = AuthXConfig()
# Устанавливаем секретный ключ для подписи JWT токенов.
config.JWT_SECRET_KEY = "super_puper_secret_key"
# Устанавливаем имя cookie, в котором будет храниться JWT токен доступа.
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
# Указываем, где AuthX должен искать JWT токен (в данном случае, в cookies).
config.JWT_TOKEN_LOCATION = ["cookies"]
# Устанавливаем время жизни токена доступа (здесь - 1 час).
config.JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

# Создаем экземпляр AuthX с примененной конфигурацией.
# Этот объект 'security' будет использоваться в приложении FastAPI
# для защиты эндпоинтов и управления аутентификацией пользователей.
security = AuthX(config=config)
