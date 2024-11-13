from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    waiting_for_city = State()  # Ожидаем выбора города
    waiting_for_direction = State()  # Ожидаем выбора направления
