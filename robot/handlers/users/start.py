from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from robot.keyboards.default.user_register import honesty_kb
from robot.states import RegisterStates
from robot.utils.misc.logging import logger, log_user_action, log_state_change, log_handler

router = Router()

@router.message(Command("start"))
@log_handler
async def bot_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "No username"
    
    log_user_action(
        user_id=user_id,
        action="Bot started",
        extra_data=f"Username: {username}, Name: {message.from_user.full_name}"
    )
    
    try:
        await message.answer(
            "👋 Привет! Добро пожаловать в программу адресной медицинской помощи.\n\n"
            "⚠️ Пожалуйста, честно ответьте на все вопросы. От этого зависит уровень поддержки.\n\n"
            "Подтвердите, что всё, что вы напишите — правда 👇",
            reply_markup=honesty_kb
        )
        
        old_state = await state.get_state()
        await state.set_state(RegisterStates.confirm_honesty)
        log_state_change(user_id, old_state, "RegisterStates.confirm_honesty")
        
        logger.info(f"Welcome message sent successfully to user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to send welcome message to user {user_id}: {str(e)}", exc_info=True)
        raise