from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton

from robot.states import RegisterStates, QuestionnaireStates

router = Router()


@router.message(RegisterStates.confirm_honesty, F.text == "✅ Я подтверждаю честность данных")
async def confirm_honesty(message: types.Message, state: FSMContext):
    await message.answer("Отлично! Напишите Ф.И.О. (Ivanov Ivan Ivanovich):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterStates.full_name)


@router.message(RegisterStates.confirm_honesty)
async def deny_honesty(message: types.Message, state: FSMContext):
    await message.answer("❌ Без подтверждения честности ты не можешь продолжить. Бот завершит работу.")
    await state.clear()


@router.message(RegisterStates.full_name)
async def get_fullname_and_proceed(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)

    await message.answer(
        f"✅ Спасибо, {message.text}!\n\n"
        "✅ Подтвердите честность предоставляемых вами данных:\n"
        "🔒 Это обязательное условие участия в программе.\n\n"
        "☐ Я подтверждаю, что все данные, которые я укажу в этой анкете, будут честными, правдивыми и соответствующими действительности.\n"
        "☐ Я осознаю, что любая попытка обмана, фальсификации документов или намеренное искажение фактов приведёт к немедленному отказу от участия в программе, как сейчас, так и в будущем.\n\n"
        "📄 Чем больше достоверных документов и доказательств вы предоставите, тем выше шансы получить максимальный процент финансовой помощи.\n\n"
        "⏱️ Срок обработки анкеты: до 3 рабочих дней. В случае одобрения с вами свяжется клиника или бот.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Я согласен с условиями")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.set_state(QuestionnaireStates.ConfirmRules)
