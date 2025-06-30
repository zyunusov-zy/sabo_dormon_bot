from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from robot.keyboards.default.user_register import honesty_kb
from robot.states import RegisterStates

router = Router()

@router.message(Command("start"))
async def bot_start(message: Message, state: FSMContext):
    await message.answer(
        "👋 Привет! Добро пожаловать в программу адресной медицинской помощи.\n\n"
        "⚠️ Пожалуйста, честно ответьте на все вопросы. От этого зависит уровень поддержки.\n\n"
        "Подтвердите, что всё, что вы напишите — правда 👇",
        reply_markup=honesty_kb
    )
    await state.set_state(RegisterStates.confirm_honesty)
