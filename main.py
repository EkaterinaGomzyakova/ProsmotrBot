import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils import executor
from dotenv import load_dotenv
import os

from handlers import router  # Проверьте, что router настроен правильно

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен бота
API_TOKEN = os.getenv('BOT_TOKEN')

# Проверка на наличие токена
if not API_TOKEN:
    raise ValueError("Токен бота не найден! Убедитесь, что .env файл содержит правильную переменную BOT_TOKEN.")

# Настроим логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Убедитесь, что роутер настроен в handlers.py и подключён правильно
dp.include_router(router)

async def main():
    # Удаляем вебхук (если используете polling, это необязательно)
    await bot.delete_webhook(drop_pending_updates=True)
    # Начинаем polling
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
