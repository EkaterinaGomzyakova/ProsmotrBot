from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

import kb
import text

import database

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
    
    await state.clear()  # Очищаем предыдущее состояние FSM
    await msg.answer(
        text.greet.format(name=msg.from_user.full_name),
        reply_markup=kb.main_menu  # Главное меню (ReplyKeyboardMarkup)
    )

    await msg.answer_photo(
        photo="https://raw.githubusercontent.com/EkaterinaGomzyakova/ProsmotrBot/refs/heads/main/images/city.png"
    )
# Обработчик кнопки "Подписаться"
@router.message(F.text == "Подписаться")
async def subscribe_handler(msg: Message, state: FSMContext):
    # Отправляем изображение перед выбором города
    await msg.answer_photo(
        photo="https://raw.githubusercontent.com/EkaterinaGomzyakova/ProsmotrBot/main/images/city.png",
        caption="Выберите ваш город:"  # Можно добавить подпись к изображению
    )

    # Отправляем кнопки выбора города
    await msg.answer("Выберите ваш город:", reply_markup=kb.city_menu)
    
    await state.set_state(Form.waiting_for_city)

# Обработчик выбора города
@router.callback_query(F.data.startswith("city_"))
async def process_city_selection(callback_query: CallbackQuery, state: FSMContext):
    city = callback_query.data.split("_")[1]  # Извлекаем название города из callback_data
    await state.update_data(city=city)  # Сохраняем выбранный город в состоянии FSM
    await callback_query.answer(f"Вы выбрали город: {city}")

    # Отправляем картинку с подписью вместо отдельного текстового сообщения
    await callback_query.message.answer_photo(
        photo="https://raw.githubusercontent.com/EkaterinaGomzyakova/ProsmotrBot/main/images/directions.png",
        caption="Теперь выберите направление:",
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

# Обработчик кнопки "Подписаться"
@router.message(F.text == "Подписаться")
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
async def get_event_city(msg: Message, state: FSMContext):
    user_data = await state.get_data()
    event_name = user_data['event_name']
    event_description = user_data['event_description']
    event_date = user_data['event_date']
    event_city = msg.text

    # Сохраняем предложение в базу данных
    database.add_event_suggestion(
        user_id=msg.from_user.id,
        event_name=event_name,
        event_description=event_description,
        event_date=event_date,
        event_city=event_city,
    )

    await msg.answer("Ваше мероприятие отправлено на модерацию. Спасибо!", reply_markup=kb.main_menu)
    await state.clear()


@router.message(Command("moderate"))
async def moderate_events(msg: Message):
    suggestions = database.get_pending_event_suggestions()

    if suggestions:
        for suggestion in suggestions:
            event_id = suggestion['id']
            text = f"Название: {suggestion['event_name']}\nОписание: {suggestion['event_description']}\nДата: {suggestion['event_date']}\nГород: {suggestion['event_city']}"
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
        await msg.answer("Нет мероприятий для модерации.")


