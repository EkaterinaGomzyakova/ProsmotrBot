import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI, Request
from dotenv import load_dotenv

import database
from handlers import router

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен из переменных окружения
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN is not set in the environment variables")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

# Создаем приложение FastAPI
app = FastAPI()

# URL для webhook
WEBHOOK_URL = f"https://fluxeventsbot.onrender.com/{API_TOKEN}"  # Замените на ваш Render-домен


# Маршрут для обработки входящих запросов от Telegram
@app.post(f"/webhook/{API_TOKEN}")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        await dp.feed_webhook_update(bot, update)
        return {"ok": True}
    except Exception as e:
        logging.error(f"Error handling webhook: {e}")
        return {"ok": False}


# Устанавливаем webhook
async def set_webhook():
    logging.info("Setting webhook...")
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен: {WEBHOOK_URL}")


# Основная асинхронная функция
async def main():
    # Установка вебхука
    await set_webhook()

    # Логирование запуска
    logging.info("Bot is up and running via webhook!")

if __name__ == "__main__":
    # Создаем таблицы, если их еще нет
    database.create_tables()

    # Настроим логирование
    logging.basicConfig(level=logging.INFO)

    # Запускаем FastAPI сервер и устанавливаем webhook
    import uvicorn
    asyncio.run(main())
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
