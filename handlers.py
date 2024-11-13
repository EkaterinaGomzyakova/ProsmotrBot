from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup

import kb
import text

# Определяем состояния
class Form(StatesGroup):
    waiting_for_city = State()
    waiting_for_direction = State()

router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
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
    await callback_query.answer(f"Вы выбрали направление: {direction}")

    # Получаем данные пользователя
    user_data = await state.get_data()
    city = user_data.get("city")
    direction = user_data.get("direction")

    # Подтверждение подписки
    await callback_query.message.answer(
        f"Вы успешно подписались на события в городе {city} по направлению {direction}.",
        reply_markup=kb.main_menu  # Возвращаем главное меню
    )
    await state.clear()  # Сбрасываем состояние FSM
