import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router

from dotenv import load_dotenv
from handlers import router  # Импортируем роутер из handlers.py

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен бота
API_TOKEN = os.getenv('BOT_TOKEN')

# Создаем экземпляр бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем роутер
dp.include_router(router)

async def main():
    # Убираем webhook, если он был
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем polling
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    # Настроим логирование
    logging.basicConfig(level=logging.INFO)

    # Запускаем основной цикл событий
    asyncio.run(main())
