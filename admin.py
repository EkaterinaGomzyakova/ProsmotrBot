from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_IDS
import database

router = Router()

# Проверка, является ли пользователь администратором
def is_admin(user_id):
    return user_id in ADMIN_IDS

# Функция рассылки подписчикам
async def send_broadcast(text, bot: Bot):
    subscribers = database.get_all_users()  # Теперь возвращает telegram_id
    for telegram_id in subscribers:
        try:
            await bot.send_message(telegram_id, text)
        except Exception as e:
            print(f"Ошибка при отправке пользователю {telegram_id}: {e}")

# Команда для отправки рассылки администраторами
@router.message(Command("broadcast"))
async def broadcast_command(msg: Message, bot: Bot):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    text = msg.text.replace("/broadcast", "").strip()
    if not text:
        await msg.answer("⚠️ Использование: /broadcast [текст рассылки]")
        return

    await msg.answer("🔄 Начинаю рассылку...")
    await send_broadcast(text, bot)
    await msg.answer("✅ Рассылка завершена.")

# Оповещение подписчиков о мероприятии
async def notify_subscribers(bot: Bot, event_name, event_description, event_date, event_city, event_direction):
    subscribers = database.get_subscribers(event_city, event_direction)

    message_text = f"📢 Новое мероприятие!\n\n" \
                   f"🏷 Название: {event_name}\n" \
                   f"📝 Описание: {event_description}\n" \
                   f"📅 Дата: {event_date}\n" \
                   f"📍 Город: {event_city}\n" \
                   f"🎭 Направление: {event_direction}"

    for telegram_id in subscribers:
        try:
            await bot.send_message(telegram_id, message_text)
        except Exception as e:
            print(f"Не удалось отправить сообщение {telegram_id}: {e}")
