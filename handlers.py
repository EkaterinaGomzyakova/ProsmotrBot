from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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

class FeedbackState(StatesGroup):  # Добавлено
    waiting_for_feedback = State()  # Состояние ожидания текста от пользователя

router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    database.add_user(msg.from_user.id, msg.from_user.full_name)
    await state.clear()  # Очищаем предыдущее состояние FSM
    await msg.answer(
        text.greet.format(name=msg.from_user.full_name),
        reply_markup=kb.main_menu  # Главное меню
    )

# Обработчик кнопки "Обратная связь"
@router.message(F.text == "Обратная связь")
async def feedback_handler(msg: Message, state: FSMContext):
    await msg.answer(
        "Пожалуйста, напишите ваш вопрос, предложение или комментарий. "
        "Мы обязательно рассмотрим ваше сообщение!"
    )
    await state.set_state(FeedbackState.waiting_for_feedback)  # Устанавливаем состояние

# Обработчик текста обратной связи
@router.message(FeedbackState.waiting_for_feedback)
async def process_feedback(msg: Message, state: FSMContext):
    feedback = msg.text  # Получаем текст от пользователя
    user_id = msg.from_user.id
    username = msg.from_user.username or "Не указан"

    # Сохраняем обратную связь в базе данных
    database.add_feedback(user_id=user_id, username=username, feedback=feedback)

    # Отвечаем пользователю
    await msg.answer("Спасибо за ваш отзыв! Мы рассмотрим его в ближайшее время.", reply_markup=kb.main_menu)
    await state.clear()  # Сбрасываем состояние FSM
