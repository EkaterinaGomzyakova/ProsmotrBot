from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

# Главное меню внизу экрана
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Подписаться")],
        [KeyboardButton(text="Подборки")],
        [KeyboardButton(text="Предложить мероприятие")],
        
    ],
    resize_keyboard=True  # Кнопки будут адаптированы по размеру
)

# Inline-кнопки для выбора города
city_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Москва", callback_data="city_Moscow")],
        [InlineKeyboardButton(text="Санкт-Петербург", callback_data="city_Saint_Petersburg")],
        [InlineKeyboardButton(text="Пермь", callback_data="city_Perm")],
        [InlineKeyboardButton(text="Екатеринбург", callback_data="city_Ekaterinburg")],
        [InlineKeyboardButton(text="Волгоград", callback_data="city_Volgograd")],
        [InlineKeyboardButton(text="Нижний Новгород", callback_data="city_Nizhny_Novgorod")],
    ]
)

# Меню выбора направления (InlineKeyboardMarkup)
direction_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Продуктовый и UX/UI-дизайн", callback_data="direction_product")],
    [InlineKeyboardButton(text="Комдиз", callback_data="direction_communication")],
    [InlineKeyboardButton(text="Моушен", callback_data="direction_motion")],
])


# Клавиатура для фильтров
filter_menu = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Тип мероприятия", callback_data="filter_type"),
        InlineKeyboardButton(text="На этой неделе", callback_data="filter_week"),
    ],
    [
        InlineKeyboardButton(text="В этом месяце", callback_data="filter_month"),
        InlineKeyboardButton(text="Бесплатные", callback_data="filter_free"),
    ],
    [
        InlineKeyboardButton(text="Онлайн", callback_data="filter_online"),
        InlineKeyboardButton(text="Применить", callback_data="apply_filters"),
    ]
])
