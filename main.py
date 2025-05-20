# main.py

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

import database
from handlers import router as handlers_router
from admin import router as admin_router, notify_subscribers

# Загрузим токен из .env
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("API_TOKEN не установлен в окружении")

# Настроим логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота с HTML-парсингом по умолчанию
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

async def reminder_loop():
    """
    Цикл отправки напоминаний:
      1) За день до мероприятия (для событий, где notified_day_before == 0)
      2) За час до мероприятия (для событий, где notified_hour_before == 0)
    Использует готовые функции из database.py.
    """
    while True:
        # Напоминания за день до
        for evt in database.get_events_for_day_reminder():
            try:
                await notify_subscribers(
                    bot,
                    evt["event_name"],
                    evt["event_description"],
                    evt["event_date"],
                    evt["event_city"],
                    evt["event_direction"]
                )
                database.mark_day_notified(evt["id"])
                logging.info(f"Sent day-before reminder for event {evt['id']}")
            except Exception as e:
                logging.error(f"Error sending day-before reminder for {evt['id']}: {e}")

        # Напоминания за час до
        for evt in database.get_events_for_hour_reminder():
            try:
                await notify_subscribers(
                    bot,
                    evt["event_name"],
                    evt["event_description"],
                    evt["event_date"],
                    evt["event_city"],
                    evt["event_direction"]
                )
                database.mark_hour_notified(evt["id"])
                logging.info(f"Sent hour-before reminder for event {evt['id']}")
            except Exception as e:
                logging.error(f"Error sending hour-before reminder for {evt['id']}: {e}")

        # Ждём минуту перед следующей проверкой
        await asyncio.sleep(60)

async def main():
    # Убедимся, что таблицы существуют (подписки и события сохраняются между перезапусками)
    database.create_tables()

    # Подключаем роутеры
    dp.include_router(handlers_router)
    dp.include_router(admin_router)

    # Запускаем цикл напоминаний в фоне
    asyncio.create_task(reminder_loop())

    # Запуск long-polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
