from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import ADMIN_IDS
import database

router = Router()

# Проверка, является ли пользователь администратором
def is_admin(user_id):
    return user_id in ADMIN_IDS

# Функция рассылки подписчикам
async def send_broadcast(text, bot: Bot):
    subscribers = database.get_all_users()
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

# Команда для модерации мероприятий
@router.message(Command("moderate"))
async def moderate_events(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    suggestions = database.get_pending_event_suggestions()

    if suggestions:
        for suggestion in suggestions:
            event_id = suggestion['id']
            text = f"🏷 Название: {suggestion['event_name']}\n" \
                   f"📝 Описание: {suggestion['event_description']}\n" \
                   f"📅 Дата: {suggestion['event_date']}\n" \
                   f"📍 Город: {suggestion['event_city']}"

            await msg.answer(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{event_id}"),
                        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{event_id}")
                    ]
                ])
            )
    else:
        await msg.answer("⚠️ Нет мероприятий для модерации.")

# Обработчик подтверждения или отклонения мероприятия
@router.callback_query(lambda c: c.data.startswith("approve_") or c.data.startswith("reject_"))
async def handle_moderation(callback_query: CallbackQuery, bot: Bot):
    action, event_id = callback_query.data.split("_")
    event_id = int(event_id)

    if action == "approve":
        event = database.approve_event(event_id)
        if event:
            await notify_subscribers(bot, event["event_name"], event["event_description"], event["event_date"], event["event_city"], event["event_direction"])
            await callback_query.message.edit_text(f"✅ Мероприятие '{event['event_name']}' одобрено и отправлено подписчикам.")
        else:
            await callback_query.message.edit_text("⚠️ Ошибка при одобрении мероприятия.")
    else:
        database.reject_event(event_id)
        await callback_query.message.edit_text("❌ Мероприятие отклонено.")

    await callback_query.answer()

# Команда для публикации мероприятий
@router.message(Command("publish"))
async def publish_event(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    await msg.answer("Введите название мероприятия:")
