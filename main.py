# main.py

import asyncio
import logging
import os
import sys
import platform
import signal
import atexit
import contextlib  # нужно в main()
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

import database
from handlers import router as handlers_router
from admin import router as admin_router, notify_subscribers  # для напоминаний

# =========================
# 0) ЗАГРУЗКА ОКРУЖЕНИЯ (.env.local > .env)
# =========================
env_path_local = Path(".env.local")
if env_path_local.exists():
    print("⚙️  Загружаю локальное окружение из .env.local")
    load_dotenv(dotenv_path=env_path_local)
else:
    load_dotenv()
    print("⚙️  Загружаю окружение из .env")

API_TOKEN = os.getenv("API_TOKEN")
RUN_BOT = os.getenv("RUN_BOT", "0")                       # запускать ли бот вообще
ALLOWED_HOSTNAME = os.getenv("ALLOWED_HOSTNAME", "")       # разрешённый хост
ENABLE_REMINDERS = os.getenv("ENABLE_REMINDERS", "0")      # включить фоновые напоминания (1/0)

if not API_TOKEN:
    raise RuntimeError("API_TOKEN не установлен в окружении")

# =========================
# 1) ЗАЩИТА ОТ СЛУЧАЙНЫХ ЗАПУСКОВ
# =========================
# 1.1. Флаг запуска
if RUN_BOT != "1":
    print("RUN_BOT != 1 — запуск бота запрещён. Выходим.")
    sys.exit(0)

# 1.2. Проверка имени хоста (если задан)
if ALLOWED_HOSTNAME:
    current_host = platform.node()
    if current_host != ALLOWED_HOSTNAME:
        print(f"Хост '{current_host}' != ALLOWED_HOSTNAME '{ALLOWED_HOSTNAME}'. Выходим.")
        sys.exit(0)

# 1.3. Защита от второй копии на том же сервере
LOCK_PATH = "/tmp/prosmotrbot.lock"
if os.path.exists(LOCK_PATH):
    print(f"Обнаружен лок-файл {LOCK_PATH}. Похоже, бот уже запущен. Выходим.")
    sys.exit(0)

with open(LOCK_PATH, "w") as f:
    f.write(str(os.getpid()))

@atexit.register
def _cleanup_lock():
    try:
        os.remove(LOCK_PATH)
    except FileNotFoundError:
        pass

# =========================
# 2) ЛОГИРОВАНИЕ
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

mode = "DEV (.env.local)" if env_path_local.exists() else "PROD (.env)"
host = platform.node()
logging.info(f"Starting bot in {mode} on host '{host}'. "
             f"RUN_BOT={RUN_BOT}, ENABLE_REMINDERS={ENABLE_REMINDERS}, ALLOWED_HOSTNAME='{ALLOWED_HOSTNAME}'")

# =========================
# 3) ИНИЦИАЛИЗАЦИЯ БОТА
# =========================
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# =========================
# 4) ФОНОВЫЕ НАПОМИНАНИЯ (ОПЦИОНАЛЬНО)
# =========================
async def reminder_loop():
    """
    Цикл напоминаний. Включается при ENABLE_REMINDERS=1 и наличии функций в database.py:
      - get_events_for_day_reminder()
      - mark_day_notified(event_id)
      - get_events_for_hour_reminder()
      - mark_hour_notified(event_id)
    Каждая функция должна работать с dict/sqlite3.Row (evt['event_name'] и т.п.).
    """
    required = [
        "get_events_for_day_reminder",
        "mark_day_notified",
        "get_events_for_hour_reminder",
        "mark_hour_notified",
    ]
    missing = [name for name in required if not hasattr(database, name)]
    if missing:
        logging.warning(f"Напоминания отключены: отсутствуют функции {missing} в database.py")
        return

    logging.info("Reminder loop started")
    while True:
        try:
            # --- За день до ---
            for evt in database.get_events_for_day_reminder():
                try:
                    await notify_subscribers(
                        bot,
                        evt["event_name"],
                        evt["event_description"],
                        evt["event_date"],
                        evt["event_city"],
                        evt["event_direction"],
                    )
                    database.mark_day_notified(evt["id"])
                    logging.info(f"Sent day-before reminder for event {evt['id']}")
                except Exception as e:
                    logging.error(f"Error in day-before reminder for id={evt.get('id')}: {e}")

            # --- За час до ---
            for evt in database.get_events_for_hour_reminder():
                try:
                    await notify_subscribers(
                        bot,
                        evt["event_name"],
                        evt["event_description"],
                        evt["event_date"],
                        evt["event_city"],
                        evt["event_direction"],
                    )
                    database.mark_hour_notified(evt["id"])
                    logging.info(f"Sent hour-before reminder for event {evt['id']}")
                except Exception as e:
                    logging.error(f"Error in hour-before reminder for id={evt.get('id')}: {e}")

            await asyncio.sleep(60)

        except asyncio.CancelledError:
            logging.info("Reminder loop cancelled")
            break
        except Exception as e:
            logging.exception(f"Reminder loop error: {e}")
            await asyncio.sleep(5)

# =========================
# 5) ГЛАВНАЯ ФУНКЦИЯ
# =========================
async def main():
    # Создаём таблицы, если их нет
    database.create_tables()

    # Подключаем роутеры
    dp.include_router(handlers_router)
    dp.include_router(admin_router)

    # Фоновый планировщик — только если включён флагом
    reminder_task = None
    if ENABLE_REMINDERS == "1":
        reminder_task = asyncio.create_task(reminder_loop())

    # Грейсфул-шатдаун
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _graceful_shutdown():
        logging.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _graceful_shutdown)
        except NotImplementedError:
            # Windows / среда без сигналов
            pass

    # Старт long polling
    await bot.delete_webhook(drop_pending_updates=True)
    polling_task = asyncio.create_task(
        dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    )

    await stop_event.wait()

    # Остановка поллинга
    polling_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await polling_task

    # Остановка напоминаний
    if reminder_task:
        reminder_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await reminder_task

    await bot.session.close()
    logging.info("Bot stopped cleanly")

# =========================
# 6) ТОЧКА ВХОДА
# =========================
if __name__ == "__main__":
    # (опционально) ускорение цикла событий на Linux, если uvloop установлен
    try:
        import uvloop
        uvloop.install()
    except Exception:
        pass

    try:
        asyncio.run(main())
    finally:
        # подстраховка (лок-файл чистится через atexit)
        try:
            os.remove(LOCK_PATH)
        except FileNotFoundError:
            pass
