from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now

from robot.states import RegisterStates, QuestionnaireStates
from robot.models import BotUser, Patient
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

async def can_register_new_patient():
    today = now().date()
    count_today = await sync_to_async(
        lambda: BotUser.objects.filter(created_at__date=today).count()
    )()
    return count_today < 20

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
        await state.update_data(phone_number=phone_number)
        user_data = await state.get_data()
        full_name = user_data.get("full_name")
        telegram_id = message.from_user.id

        # Проверка на уже зарегистрированного пользователя
        existing_user = await sync_to_async(BotUser.objects.filter(
            telegram_id=telegram_id,
            phone_number=phone_number
        ).first)()

        if existing_user:
            # Проверяем есть ли у пользователя пациент (должен быть только один)
            try:
                existing_patient = await sync_to_async(lambda: existing_user.patient)()
                
                # Проверяем может ли подать новую анкету
                can_register = await sync_to_async(existing_patient.can_register_again)()
                
                if not can_register:
                    if existing_patient.is_fully_approved:
                        # Одобрен менее 7 месяцев назад
                        months_left = 7 - ((timezone.now() - existing_patient.approved_at).days // 30)
                        await message.answer(
                            f"❗Вы уже получили одобрение {existing_patient.approved_at.strftime('%d.%m.%Y')}.\n"
                            f"Повторная подача анкеты возможна через {months_left} месяцев."
                        )
                        return
                    else:
                        # Анкета на рассмотрении
                        await message.answer(
                            "❗У вас уже есть анкета на рассмотрении. "
                            "Дождитесь завершения проверки перед повторной отправкой."
                        )
                        return
                else:
                    if existing_patient.is_rejected:
                        await message.answer(
                            "❗Ранее ваша анкета была отклонена."
                            "Вы можете снова пройти регистрацию, однако необходимо указать другой диагноз, отличный от предыдущего.\nВ противном случае анкета будет отклонена повторно."
                        )
                        # Удаляем старую запись пациента для создания новой
                        await sync_to_async(existing_patient.delete)()
                    elif existing_patient.is_fully_approved:
                        await message.answer(
                            "✅ Прошло 7 месяцев с момента одобрения. "
                            "Вы можете подать новую анкету."
                        )
                        # Удаляем старую запись пациента для создания новой
                        await sync_to_async(existing_patient.delete)()
                        
            except Patient.DoesNotExist:
                # У пользователя нет записи пациента, можно создать
                await message.answer("✅ Вы уже зарегистрированы. Переходим к анкете.")
        else:
            can_register_today = await can_register_new_patient()
            if not can_register_today:
                await message.answer(
                    "❗ Сегодня достигнут лимит регистрации.\n"
                    "Пожалуйста, попробуйте снова завтра."
                )
                return

            # Новый пользователь
            await sync_to_async(BotUser.objects.create)(
                telegram_id=telegram_id,
                full_name=full_name,
                phone_number=phone_number
            )

        # Показываем правила и переходим к анкете
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

        logger.info(f"User {user_id} successfully processed registration and moved to questionnaire")

    except Exception as e:
        log_error(user_id, e, "get_phone_number_and_confirm_rules handler", "RegisterStates.phone_number")
        raise