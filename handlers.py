from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup

import kb
import text

import database

# Определяем состояния
class Form(StatesGroup):
    waiting_for_city = State()
    waiting_for_direction = State()

class FilterState(StatesGroup):
    choosing_filters = State()
    applying_filters = State()

router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    database.add_user(msg.from_user.id, msg.from_user.full_name)
    
    await state.clear()  # Очищаем предыдущее состояние FSM
    await msg.answer(
        text.greet.format(name=msg.from_user.full_name),
        reply_markup=kb.main_menu  # Главное меню (ReplyKeyboardMarkup)
    )

# Обработчик кнопки "Подписаться"
@router.message(F.text == "Подписаться")
async def subscribe_handler(msg: Message, state: FSMContext):
    await msg.answer("Выберите ваш город:", reply_markup=kb.city_menu)  # Inline-кнопки с городами
    await state.set_state(Form.waiting_for_city)

# Обработчик выбора города
@router.callback_query(F.data.startswith("city_"))
async def process_city_selection(callback_query: CallbackQuery, state: FSMContext):
    city = callback_query.data.split("_")[1]  # Извлекаем название города из callback_data
    await state.update_data(city=city)  # Сохраняем выбранный город в состоянии FSM
    await callback_query.answer(f"Вы выбрали город: {city}")

    # Отправляем новое сообщение с выбором направления, не удаляя выбор города
    await callback_query.message.reply(
        "Теперь выберите направление:",
        reply_markup=kb.direction_menu  # Inline-кнопки с направлениями
    )
    await state.set_state(Form.waiting_for_direction)

# Обработчик выбора направления
@router.callback_query(F.data.startswith("direction_"))
async def process_direction_selection(callback_query: CallbackQuery, state: FSMContext):
    direction = callback_query.data.split("_")[1]  # Извлекаем направление из callback_data
    await state.update_data(direction=direction)  # Сохраняем направление в состоянии FSM

    # Получаем сохраненные данные
    user_data = await state.get_data()
    city = user_data.get("city")

    # Сохраняем подписку
    user_id = database.get_user_id(callback_query.from_user.id)
    if user_id:
        database.add_subscription(user_id, city, direction)
        await callback_query.answer(f"Вы подписались на {direction} в {city}.")
    else:
        await callback_query.answer("Ошибка: пользователь не найден в базе данных.")
    
    # Подтверждение подписки
    await callback_query.message.answer(
        f"Вы успешно подписались на события в городе {city} по направлению {direction}.",
        reply_markup=kb.main_menu  # Возвращаем главное меню
    )
    await state.clear()  # Сбрасываем состояние FSM

# Обработчик кнопки "Мои подписки"
@router.message(F.text == "Мои подписки")
async def show_subscriptions(msg: Message):
    user_id = database.get_user_id(msg.from_user.id)
    if user_id:
        subscriptions = database.get_subscriptions(user_id)
        if subscriptions:
            subscriptions_text = "\n".join([f"{city} - {direction}" for city, direction in subscriptions])
            text = f"Ваши подписки:\n{subscriptions_text}"
        else:
            text = "У вас пока нет подписок."
    else:
        text = "Ошибка: пользователь не найден в базе данных."

    await msg.answer(text)

# Обработчик кнопки "Подборки"
@router.message(F.text == "Подборки")
async def show_filter_menu(msg: Message, state: FSMContext):
    await msg.answer(
        "Выберите фильтры для мероприятий:",
        reply_markup=kb.filter_menu
    )
    await state.set_state(FilterState.choosing_filters)

# Обработчики фильтров
@router.callback_query(F.data.startswith("filter_"))
async def process_filter_selection(callback_query: CallbackQuery, state: FSMContext):
    filter_type = callback_query.data.split("_")[1]
    
    # Сохраняем выбранный фильтр
    user_filters = await state.get_data()
    selected_filters = user_filters.get("selected_filters", [])
    if filter_type not in selected_filters:
        selected_filters.append(filter_type)
    else:
        selected_filters.remove(filter_type)  # Убираем фильтр, если его выбирают повторно

    await state.update_data(selected_filters=selected_filters)

    # Отправляем подтверждение
    await callback_query.answer(f"Вы выбрали: {filter_type.capitalize()}")

# Обработчик применения фильтров
@router.callback_query(F.data == "apply_filters")
async def apply_filters(callback_query: CallbackQuery, state: FSMContext):
    user_filters = await state.get_data()
    selected_filters = user_filters.get("selected_filters", [])
    
    # Применяем выбранные фильтры (пример)
    if selected_filters:
        filters_text = ", ".join(selected_filters)
        await callback_query.message.answer(f"Применены фильтры: {filters_text}")
    else:
        await callback_query.message.answer("Вы не выбрали ни одного фильтра.")

    # Возвращаем главное меню
    await callback_query.message.answer(
        "Возвращаюсь в главное меню:",
        reply_markup=kb.main_menu
    )
    await state.clear()
