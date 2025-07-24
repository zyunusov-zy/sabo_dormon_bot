from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from asgiref.sync import sync_to_async

from robot.states import RegisterStates, QuestionnaireStates
from robot.models import BotUser
from robot.utils.misc.logging import logger, log_user_action, log_state_change, log_handler, log_error

router = Router()


@router.message(RegisterStates.confirm_honesty, F.text == "✅ Я подтверждаю честность данных")
@log_handler
async def confirm_honesty(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    log_user_action(
        user_id=user_id,
        action="Confirmed honesty",
        state="RegisterStates.confirm_honesty"
    )
    try:
        await message.answer("Отлично! Напишите Ф.И.О. (Ivanov Ivan Ivanovich):", reply_markup=ReplyKeyboardRemove())
        
        old_state = await state.get_state()
        await state.set_state(RegisterStates.full_name)
        log_state_change(user_id, old_state, "RegisterStates.full_name")
        
    except Exception as e:
        log_error(user_id, e, "confirm_honesty handler", "RegisterStates.confirm_honesty")
        raise

@log_handler
async def deny_honesty(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    log_user_action(
        user_id=user_id,
        action="Denied honesty - session terminated",
        state="RegisterStates.confirm_honesty",
        extra_data=f"Message: {message.text}"
    )
    
    try:
        await message.answer("❌ Без подтверждения честности ты не можешь продолжить. Бот завершит работу.")
        await state.clear()
        
        logger.warning(f"User {user_id} denied honesty agreement - session cleared")
        
    except Exception as e:
        log_error(user_id, e, "deny_honesty handler", "RegisterStates.confirm_honesty")
        raise



@router.message(RegisterStates.full_name)
async def get_fullname_and_ask_phone(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    full_name = message.text.strip()
    
    log_user_action(
        user_id=user_id,
        action="Provided full name",
        state="RegisterStates.full_name",
        extra_data=f"Name: {full_name}"
    )
    
    try:
        await state.update_data(full_name=full_name)
        
        await message.answer(
            "📱 Пожалуйста, отправьте ваш номер телефона, нажав кнопку ниже:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        
        old_state = await state.get_state()
        await state.set_state(RegisterStates.phone_number)
        log_state_change(user_id, old_state, "RegisterStates.phone_number")
        
    except Exception as e:
        log_error(user_id, e, "get_fullname_and_ask_phone handler", "RegisterStates.full_name")
        raise


@router.message(RegisterStates.phone_number, F.contact)
async def get_phone_number_and_confirm_rules(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    contact = message.contact
    phone_number = contact.phone_number
    
    log_user_action(
        user_id=user_id,
        action="Provided phone number",
        state="RegisterStates.phone_number",
        extra_data=f"Phone: {phone_number}"
    )
    try:
        await state.update_data(phone_number=contact.phone_number)


        user_data = await state.get_data()
        full_name = user_data.get("full_name")
        phone_number = contact.phone_number
        telegram_id = message.from_user.id

        await sync_to_async(BotUser.objects.update_or_create)(
            telegram_id=telegram_id,
            defaults={
                "full_name": full_name,
                "phone_number": phone_number
            }
        )
        await message.answer(
            "✅ Спасибо!\n\n"
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
        old_state = await state.get_state()
        await state.set_state(QuestionnaireStates.ConfirmRules)
        log_state_change(user_id, old_state, "QuestionnaireStates.ConfirmRules")
        
        logger.info(f"User {user_id} successfully registered and moved to questionnaire")
    except Exception as e:
        log_error(user_id, e, "get_phone_number_and_confirm_rules handler", "RegisterStates.phone_number")
        raise
