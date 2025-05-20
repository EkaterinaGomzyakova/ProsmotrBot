from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔍 Найти мероприятия"),
            KeyboardButton(text="⭐ Мои подписки")
        ],
        [
            KeyboardButton(text="➕ Предложить мероприятие")
        ],
    ],
    resize_keyboard=True
)

# Меню выбора города
city_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Москва",           callback_data="city_Moscow")],
    [InlineKeyboardButton(text="Санкт-Петербург", callback_data="city_Saint_Petersburg")],
    [InlineKeyboardButton(text="Пермь",            callback_data="city_Perm")],
    [InlineKeyboardButton(text="Екатеринбург",     callback_data="city_Ekaterinburg")],
    [InlineKeyboardButton(text="Волгоград",        callback_data="city_Volgograd")],
    [InlineKeyboardButton(text="Нижний Новгород",  callback_data="city_Nizhny_Novgorod")],
])

# Меню выбора направления
direction_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Продуктовый и UX/UI-дизайн", callback_data="direction_product")],
    [InlineKeyboardButton(text="Комдиз",                      callback_data="direction_communication")],
    [InlineKeyboardButton(text="Моушен-дизайн",               callback_data="direction_motion")],
])
