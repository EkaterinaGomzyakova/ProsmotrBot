# admin.py

from aiogram import Router, Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.filters import Command

import database
from config import ADMIN_IDS

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def notify_admins_about_event(
    bot: Bot,
    event_id: int,
    event_name: str,
    event_description: str,
    event_datetime: str,
    event_city: str,
    event_direction: str
):
    """
    Оповестить всех администраторов о новом предложенном событии,
    прикрепив к сообщению inline-кнопки «Одобрить»/«Отклонить».
    """
    text = (
        f"📢 <b>Новое мероприятие на модерацию!</b>\n\n"
        f"🏷 <b>Название:</b> {event_name}\n"
        f"📝 <b>Описание:</b> {event_description}\n"
        f"🗓 <b>Дата и время:</b> {event_datetime}\n"
        f"📍 <b>Город:</b> {event_city}\n"
        f"🎭 <b>Направление:</b> {event_direction}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{event_id}"),
            InlineKeyboardButton(text="❌ Отклонить",  callback_data=f"reject_{event_id}")
        ]
    ])
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Ошибка при отправке модерации администратору {admin_id}: {e}")

async def notify_subscribers(
    bot: Bot,
    event_name: str,
    event_description: str,
    event_datetime: str,
    event_city: str,
    event_direction: str
):
    """
    Рассылает напоминание о событии всем подписчикам указанного города+направления.
    """
    subs = database.get_subscribers(event_city, event_direction)
    if not subs:
        return

    text = (
        f"📢 Напоминание о мероприятии!\n\n"
        f"💥 {event_name}\n"
        f"📍 {event_city} ({event_direction})\n"
        f"🗓 {event_datetime}\n\n"
        f"{event_description}"
    )
    for tg_id in subs:
        try:
            await bot.send_message(chat_id=tg_id, text=text)
        except Exception as e:
            print(f"Не удалось отправить подписчику {tg_id}: {e}")


@router.callback_query(lambda c: c.data.startswith("approve_") or c.data.startswith("reject_"))
async def moderation_handler(callback_query: CallbackQuery, bot: Bot):
    action, raw_id = callback_query.data.split("_", 1)
    event_id = int(raw_id)

    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("❌ У вас нет прав на модерацию.", show_alert=True)

    if action == "approve":
        event = database.approve_event(event_id)
        if not event:
            await callback_query.message.edit_text("⚠️ Ошибка при одобрении.")
            return await callback_query.answer()

        # Сброс флагов, чтобы напоминания ушли по расписанию
        database.mark_day_notified(event_id)
        database.mark_hour_notified(event_id)

        # Формируем карточку для подписчиков и админов
        broadcast_text = (
            f"📢 <b>Мероприятие одобрено!</b>\n\n"
            f"💥 {event['event_name']}\n"
            f"📍 {event['event_city']} ({event['event_direction']})\n"
            f"🗓 {event['event_date']}\n\n"
            f"{event['event_description']}"
        )
        recipients = set(database.get_subscribers(event["event_city"], event["event_direction"])) | set(ADMIN_IDS)
        for tg_id in recipients:
            try:
                await bot.send_message(chat_id=tg_id, text=broadcast_text, parse_mode="HTML")
            except Exception as e:
                print(f"Не удалось разослать {tg_id}: {e}")

        await callback_query.message.edit_text(
            f"✅ Событие «{event['event_name']}» одобрено и разослано всем."
        )

    else:  # reject
        database.reject_event(event_id)
        await callback_query.message.edit_text("❌ Мероприятие отклонено.")

    await callback_query.answer()


@router.message(Command("broadcast"))
async def broadcast_command(msg: Message, bot: Bot):
    """
    /broadcast <текст>
    Рассылает любое сообщение всем пользователям и администраторам.
    """
    if not is_admin(msg.from_user.id):
        return await msg.reply("❌ У вас нет прав для этой команды.")

    text_to_send = msg.text.removeprefix("/broadcast").strip()
    if not text_to_send:
        return await msg.reply("⚠️ Использование: /broadcast <текст рассылки>")

    await msg.reply("🔄 Начинаю рассылку…")

    all_users = database.get_all_users()
    recipients = set(all_users) | set(ADMIN_IDS)
    for tg_id in recipients:
        try:
            await bot.send_message(chat_id=tg_id, text=text_to_send)
        except Exception as e:
            print(f"Ошибка при доставке {tg_id}: {e}")

    await msg.reply("✅ Рассылка завершена.")
