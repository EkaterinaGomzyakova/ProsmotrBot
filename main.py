import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers import router as handlers_router
from admin import router as admin_router  # Подключаем роутер админки
import database

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен из переменных окружения
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN is not set in the environment variables")

# Инициализация бота
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)

# Инициализация диспетчера
dp = Dispatcher(storage=MemoryStorage())

# Основная асинхронная функция
async def main():
    dp.include_router(handlers_router)  # Подключаем обработчики пользователей
    dp.include_router(admin_router)  # Подключаем обработчики админки
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    # Создаем таблицы, если их еще нет
    database.create_tables()

    # Настроим логирование
    logging.basicConfig(level=logging.INFO)

    # Запускаем основной цикл событий
    asyncio.run(main())
