from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup

import kb
import text
import database
from config import ADMIN_IDS
from admin import notify_admins_about_event
from database import add_event


# Определяем состояния
class Form(StatesGroup):
    waiting_for_city = State()
    waiting_for_direction = State()
    waiting_for_event_name = State()
    waiting_for_event_description = State()
    waiting_for_event_date = State()
    waiting_for_event_city = State()

class FilterState(StatesGroup):
    choosing_filters = State()
    applying_filters = State()

router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    database.add_user(msg.from_user.id, msg.from_user.full_name)
    await state.clear()
    
    await msg.answer(
        text.greet.format(name=msg.from_user.full_name),
        reply_markup=kb.main_menu
    )
    await msg.answer_photo(photo="https://raw.githubusercontent.com/EkaterinaGomzyakova/ProsmotrBot/main/images/city.png")

# Обработчик подписки
@router.message(F.text == "Подписаться")
async def subscribe_handler(msg: Message, state: FSMContext):
    await msg.answer_photo(
        photo="https://raw.githubusercontent.com/EkaterinaGomzyakova/ProsmotrBot/main/images/city.png",
        caption="Выберите ваш город:"
    )
    await msg.answer("Выберите ваш город:", reply_markup=kb.city_menu)
    await state.set_state(Form.waiting_for_city)

# Выбор города
@router.callback_query(F.data.startswith("city_"))
async def process_city_selection(callback_query: CallbackQuery, state: FSMContext):
    city = callback_query.data.split("_")[1]
    await state.update_data(city=city)
    await callback_query.answer(f"Вы выбрали город: {city}")
    await callback_query.message.reply("Теперь выберите направление:", reply_markup=kb.direction_menu)
    await state.set_state(Form.waiting_for_direction)

# Выбор направления
@router.callback_query(F.data.startswith("direction_"))
async def process_direction_selection(callback_query: CallbackQuery, state: FSMContext):
    direction = callback_query.data.split("_")[1]
    user_data = await state.get_data()
    city = user_data.get("city")

    database.add_subscription(callback_query.from_user.id, city, direction)

    await callback_query.answer(f"Вы подписались на {direction} в {city}.")
    await callback_query.message.answer(f"Вы подписаны на события в {city}, направление: {direction}.", reply_markup=kb.main_menu)
    await state.clear()

# Просмотр подписок
@router.message(F.text == "Мои подписки")
async def show_subscriptions(msg: Message):
    subscriptions = database.get_subscriptions(msg.from_user.id)
    if subscriptions:
        subscriptions_text = "\n".join([f"{city} - {direction}" for city, direction in subscriptions])
        text = f"Ваши подписки:\n{subscriptions_text}"
    else:
        text = "У вас пока нет подписок."

    await msg.answer(text)

# Фильтры
@router.message(F.text == "Подборки")
async def show_filter_menu(msg: Message, state: FSMContext):
    await msg.answer("Выберите фильтры для мероприятий:", reply_markup=kb.filter_menu)
    await state.set_state(FilterState.choosing_filters)

# Обработчики фильтров
@router.callback_query(F.data.startswith("filter_"))
async def process_filter_selection(callback_query: CallbackQuery, state: FSMContext):
    filter_type = callback_query.data.split("_")[1]
    user_filters = await state.get_data()
    selected_filters = user_filters.get("selected_filters", [])

    if filter_type in selected_filters:
        selected_filters.remove(filter_type)
    else:
        selected_filters.append(filter_type)

    await state.update_data(selected_filters=selected_filters)
    await callback_query.answer(f"Вы выбрали: {filter_type.capitalize()}")

# Применение фильтров
@router.callback_query(F.data == "apply_filters")
async def apply_filters(callback_query: CallbackQuery, state: FSMContext):
    user_filters = await state.get_data()
    selected_filters = user_filters.get("selected_filters", [])

    if selected_filters:
        filters_text = ", ".join(selected_filters)
        await callback_query.message.answer(f"Применены фильтры: {filters_text}")
    else:
        await callback_query.message.answer("Вы не выбрали ни одного фильтра.")

    await callback_query.message.answer("Возвращаюсь в главное меню:", reply_markup=kb.main_menu)
    await state.clear()

# Предложить мероприятие
@router.message(F.text == "Предложить мероприятие")
async def propose_event(msg: Message, state: FSMContext):
    await msg.answer("Введите название мероприятия:")
    await state.set_state(Form.waiting_for_event_name)

@router.message(Form.waiting_for_event_name)
async def get_event_name(msg: Message, state: FSMContext):
    await state.update_data(event_name=msg.text)
    await msg.answer("Опишите мероприятие:")
    await state.set_state(Form.waiting_for_event_description)

@router.message(Form.waiting_for_event_description)
async def get_event_description(msg: Message, state: FSMContext):
    await state.update_data(event_description=msg.text)
    await msg.answer("Укажите дату мероприятия (в формате ГГГГ-ММ-ДД):")
    await state.set_state(Form.waiting_for_event_date)

@router.message(Form.waiting_for_event_date)
async def get_event_date(msg: Message, state: FSMContext):
    await state.update_data(event_date=msg.text)
    await msg.answer("Введите город мероприятия:")
    await state.set_state(Form.waiting_for_event_city)
    
@router.message(Form.waiting_for_event_city)
async def get_event_city(msg: Message, state: FSMContext, bot: Bot):
    print("Обработчик get_event_city вызван")  # Проверяем, что обработчик запускается
    user_data = await state.get_data()
    print("user_data:", user_data)  # Проверяем, что данные есть

    event_name = user_data.get('event_name')
    event_description = user_data.get('event_description')
    event_date = user_data.get('event_date')
    event_city = msg.text

    # Проверяем, есть ли все данные
    if not event_name or not event_description or not event_date:
        await msg.answer("⚠ Произошла ошибка! Попробуйте начать заново.", reply_markup=kb.main_menu)
        await state.clear()
        return

    # Пробуем добавить в базу
    try:
        event_id = database.add_event(event_name, event_description, event_city, "", event_date, 0)



        print(f"Мероприятие добавлено в БД с ID {event_id}")
    except Exception as e:
        print("Ошибка при добавлении мероприятия в БД:", e)
        await msg.answer("⚠ Ошибка при сохранении мероприятия. Попробуйте позже.")
        return

    await msg.answer("✅ Ваше мероприятие отправлено на модерацию!", reply_markup=kb.main_menu)

    # Пробуем уведомить админов
    try:
        await notify_admins_about_event(bot, event_id, event_name, event_description, event_date, event_city)
        print("Уведомление админам отправлено")
    except Exception as e:
        print("Ошибка при уведомлении админов:", e)
        await msg.answer(f"⚠ Ошибка при уведомлении админов: {e}")

    await state.clear()
