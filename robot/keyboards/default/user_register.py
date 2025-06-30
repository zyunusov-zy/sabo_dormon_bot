
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

honesty_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Я подтверждаю честность данных")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)