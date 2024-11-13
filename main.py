import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from dotenv import load_dotenv
import os

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен бота из переменной окружения
API_TOKEN = os.getenv('BOT_TOKEN')

# Проверка, что токен был загружен
if not API_TOKEN:
    raise ValueError("Токен бота не найден! Убедитесь, что .env файл содержит правильную переменную BOT_TOKEN.")

async def main():
    # Создаем бота с токеном, полученным из .env
    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Включаем обработчики роутеров
    dp.include_router(router)
    
    # Удаляем webhook и начинаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
