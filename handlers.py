# handlers.py

from datetime import date, datetime

from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

import database
import text
from admin import notify_admins_about_event, notify_subscribers

router = Router()

# =========================
# ВСТРОЕННЫЕ КЛАВИАТУРЫ (перенос из kb.py)
# =========================
city_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Москва",           callback_data="city_Moscow")],
    [InlineKeyboardButton(text="Санкт-Петербург", callback_data="city_Saint_Petersburg")],
    [InlineKeyboardButton(text="Пермь",           callback_data="city_Perm")],
    [InlineKeyboardButton(text="Екатеринбург",    callback_data="city_Ekaterinburg")],
    [InlineKeyboardButton(text="Волгоград",       callback_data="city_Volgograd")],
    [InlineKeyboardButton(text="Нижний Новгород", callback_data="city_Nizhny_Novgorod")],
])

direction_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Продуктовый и UX/UI-дизайн", callback_data="direction_product")],
    [InlineKeyboardButton(text="Комдиз",                      callback_data="direction_communication")],
    [InlineKeyboardButton(text="Моушен-дизайн",               callback_data="direction_motion")],
])

# =========================
# Состояния
# =========================
class Form(StatesGroup):
    # Подписка
    waiting_for_city_sub          = State()
    waiting_for_direction_sub     = State()
    # Ручной поиск
    waiting_for_city_search       = State()
    waiting_for_direction_search  = State()
    # Предложить событие
    waiting_for_event_direction   = State()
    waiting_for_event_city        = State()
    waiting_for_event_name        = State()
    waiting_for_event_description = State()
    waiting_for_event_date        = State()
    waiting_for_event_time        = State()


@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    database.add_user(msg.from_user.id, msg.from_user.full_name)
    await state.clear()
    # Предложим сразу подписаться через /subscribe
    await msg.answer(
        text.greet.format(name=msg.from_user.full_name) +
        "\n\nЧтобы получать подборки событий — используйте команду /subscribe"
    )


# — Подписка —
@router.message(Command("subscribe"))
async def subscribe_start(msg: Message, state: FSMContext):
    database.add_user(msg.from_user.id, msg.from_user.full_name)
    await msg.answer("Выберите город для подписки:", reply_markup=city_menu)
    await state.set_state(Form.waiting_for_city_sub)


@router.callback_query(F.data.startswith("city_"), StateFilter(Form.waiting_for_city_sub))
async def sub_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split("_", 1)[1]
    await state.update_data(city=city)
    await callback.answer(f"Город: {city}")
    await callback.message.answer("Теперь направление:", reply_markup=direction_menu)
    await state.set_state(Form.waiting_for_direction_sub)


@router.callback_query(F.data.startswith("direction_"), StateFilter(Form.waiting_for_direction_sub))
async def sub_direction(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    direction = callback.data.split("_", 1)[1]
    database.add_subscription(callback.from_user.id, data["city"], direction)
    await callback.answer(f"Подписка: {data['city']} — {direction}")
    await callback.message.answer(
        "Готово! Буду напоминать за день и за час до события."
    )
    await state.clear()


# — Ручной поиск —
@router.message(Command("pack"))
async def search_start(msg: Message, state: FSMContext):
    await msg.answer("Выберите город для поиска:", reply_markup=city_menu)
    await state.set_state(Form.waiting_for_city_search)


@router.callback_query(F.data.startswith("city_"), StateFilter(Form.waiting_for_city_search))
async def search_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split("_", 1)[1]
    await state.update_data(search_city=city)
    await callback.answer(f"Город: {city}")
    await callback.message.answer("Теперь направление:", reply_markup=direction_menu)
    await state.set_state(Form.waiting_for_direction_search)


@router.callback_query(F.data.startswith("direction_"), StateFilter(Form.waiting_for_direction_search))
async def search_direction(callback: CallbackQuery, state: FSMContext):
    data      = await state.get_data()
    city      = data["search_city"]
    direction = callback.data.split("_", 1)[1]
    events    = database.get_events_by_filter(city, direction)

    if not events:
        await callback.message.answer("Ничего не найдено.")
    else:
        for evt in events:
            photo = evt.get("image_url") or text.default_event_image
            caption = (
                f"💥 {evt['event_name']}\n"
                f"📍 {evt['event_city']} ({direction})\n\n"
                f"🗓 {evt['event_date']}\n\n"
                f"Описание:\n{evt['event_description']}"
            )
            await callback.message.answer_photo(photo=photo, caption=caption)

    await state.clear()


# — Предложить событие —
@router.message(Command("add"))
async def propose_start(msg: Message, state: FSMContext):
    database.add_user(msg.from_user.id, msg.from_user.full_name)
    await msg.answer("Выберите направление события:", reply_markup=direction_menu)
    await state.set_state(Form.waiting_for_event_direction)


@router.callback_query(F.data.startswith("direction_"), StateFilter(Form.waiting_for_event_direction))
async def propose_direction(callback: CallbackQuery, state: FSMContext):
    direction = callback.data.split("_", 1)[1]
    await state.update_data(event_direction=direction)
    await callback.answer(f"Направление: {direction}")
    await callback.message.answer("Теперь город мероприятия:", reply_markup=city_menu)
    await state.set_state(Form.waiting_for_event_city)


@router.callback_query(F.data.startswith("city_"), StateFilter(Form.waiting_for_event_city))
async def propose_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split("_", 1)[1]
    await state.update_data(event_city=city)
    await callback.answer(f"Город: {city}")
    await callback.message.answer("Введите название мероприятия:")
    await state.set_state(Form.waiting_for_event_name)


@router.message(Form.waiting_for_event_name)
async def propose_name(msg: Message, state: FSMContext):
    await state.update_data(event_name=msg.text)
    await msg.answer("Опишите мероприятие:")
    await state.set_state(Form.waiting_for_event_description)


@router.message(Form.waiting_for_event_description)
async def propose_desc(msg: Message, state: FSMContext):
    await state.update_data(event_description=msg.text)
    kb_cal = await SimpleCalendar().start_calendar()
    await msg.answer("Выберите дату мероприятия:", reply_markup=kb_cal)
    await state.set_state(Form.waiting_for_event_date)


@router.callback_query(SimpleCalendarCallback.filter(), StateFilter(Form.waiting_for_event_date))
async def process_calendar(
    callback: CallbackQuery,
    callback_data: SimpleCalendarCallback,
    state: FSMContext
):
    cal = SimpleCalendar()
    selected, picked = await cal.process_selection(callback, callback_data)
    if not selected:
        return

    picked_date = picked.date() if isinstance(picked, datetime) else picked

    if picked_date < date.today():
        await callback.answer(
            "⚠️ Можно выбрать только дату от сегодня и позже.",
            show_alert=True
        )
        kb_cal = await cal.start_calendar()
        await callback.message.edit_reply_markup(reply_markup=kb_cal)
        return

    await state.update_data(event_date=picked_date.strftime("%Y-%m-%d"))
    await callback.message.answer(
        f"Дата выбрана: {picked_date.strftime('%Y-%m-%d')}\n"
        "Теперь введите время в формате ЧЧ:ММ:"
    )
    await state.set_state(Form.waiting_for_event_time)


@router.message(Form.waiting_for_event_time)
async def process_event_time(msg: Message, state: FSMContext, bot: Bot):
    time_text = msg.text.strip()
    try:
        h, m = map(int, time_text.split(":"))
        assert 0 <= h < 24 and 0 <= m < 60
    except Exception:
        return await msg.answer("❌ Неверный формат времени. Введите ЧЧ:ММ.")

    data = await state.get_data()
    dt_str = f"{data['event_date']} {time_text}"
    event_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

    if event_dt < datetime.now():
        return await msg.answer(
            "❌ Нельзя указать время в прошлом. Пожалуйста, введите будущее время."
        )

    eid = database.add_event(
        data["event_name"],
        data["event_description"],
        data["event_city"],
        data["event_direction"],
        dt_str,
        is_approved=0
    )

    # Уведомляем админов об одном конкретном событии
    await notify_admins_about_event(
        bot=bot,
        event_id=eid,
        event_name=data["event_name"],
        event_description=data["event_description"],
        event_datetime=dt_str,
        event_city=data["event_city"],
        event_direction=data["event_direction"]
    )

    await msg.answer(
        "✅ Событие отправлено на модерацию. После одобрения я сообщу подписчикам."
    )

    await state.clear()
