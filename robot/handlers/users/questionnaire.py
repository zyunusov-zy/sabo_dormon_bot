from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Message
from aiogram3_calendar.simple_calendar import SimpleCalendar, SimpleCalendarCallback

import re

from aiogram import Router
from aiogram.filters import StateFilter
from robot.states import QuestionnaireStates


router = Router()


@router.message(StateFilter(QuestionnaireStates.ConfirmRules))
async def confirm_rules(message: types.Message, state: FSMContext):
    if message.text == "✅ Я согласен с условиями":
        await message.answer(
            "Анкета началась 📝\n\n1️⃣ Введите Ф.И.О. пациента полностью (пример: Ivanov Ivan Ivanovich):", 
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(QuestionnaireStates.Q1_FullName)
    else:
        await message.answer("⚠️ Вы должны подтвердить условия участия для продолжения.")


@router.message(StateFilter(QuestionnaireStates.Q1_FullName))
async def questionnaire_full_name(message: types.Message, state: FSMContext):
    await state.update_data(q1_full_name=message.text)

    await message.answer(
        "2️⃣ Выберите дату рождения пациента 📅",
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(QuestionnaireStates.Q2_BirthDate)


@router.callback_query(SimpleCalendarCallback.filter(), StateFilter(QuestionnaireStates.Q2_BirthDate))
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(q2_birth_date=date.strftime("%d.%m.%Y"))

        gender_markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await callback_query.message.answer("3️⃣ Укажите пол пациента:", reply_markup=gender_markup)
        await state.set_state(QuestionnaireStates.Q3_Gender)
        await callback_query.answer()
        

@router.message(StateFilter(QuestionnaireStates.Q3_Gender))
async def questionnaire_gender(message: types.Message, state: FSMContext):
    gender = message.text.lower()
    if gender not in ["мужской", "женский"]:
        await message.answer("❌ Пожалуйста, выберите один из вариантов: Мужской или Женский.")
        return

    await state.update_data(q3_gender=gender.capitalize())

    await message.answer("4️⃣ Введите номер телефона пациента:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(QuestionnaireStates.Q4_PhoneNumber)


@router.message(StateFilter(QuestionnaireStates.Q4_PhoneNumber))
async def questionnaire_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not re.match(r"^\+?\d{9,15}$", phone):
        await message.answer("❌ Введите номер телефона в международном формате (например: +998901234567).")
        return

    await state.update_data(q4_phone_number=phone)
    await message.answer("5️⃣ Введите ваш Telegram username (начиная с @):")
    await state.set_state(QuestionnaireStates.Q5_TelegramUsername)


regions = ["Ташкент", "Самарканд", "Фергана", "Андижан", "Бухара", "Хорезм", "Навои", "Наманган", "Кашкадарья", "Сурхандарья", "Сырдарья", "Джизак", "Каракалпакстан"]

@router.message(StateFilter(QuestionnaireStates.Q5_TelegramUsername))
async def questionnaire_telegram(message: types.Message, state: FSMContext):
    username = message.text.strip()
    if not re.match(r"^@[\w\d_]{5,}$", username):
        await message.answer("❌ Введите корректный Telegram username, начинающийся с @.")
        return

    await state.update_data(q5_telegram_username=username)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=region)] for region in regions],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer("6️⃣ Выберите регион проживания или прописки 📍:", reply_markup=keyboard)
    await state.set_state(QuestionnaireStates.Q6_Region)
    

@router.message(StateFilter(QuestionnaireStates.Q6_Region))
async def questionnaire_region(message: types.Message, state: FSMContext):
    await state.update_data(q6_region=message.text)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Сам(а)")], [KeyboardButton(text="Родственник")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer("7️⃣ Кто обращается?", reply_markup=keyboard)
    await state.set_state(QuestionnaireStates.Q7_WhoApplies)


@router.message(StateFilter(QuestionnaireStates.Q7_WhoApplies))
async def questionnaire_who_applies(message: types.Message, state: FSMContext):
    await state.update_data(q7_who_applies=message.text)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да")],
            [KeyboardButton(text="Нет")],
            [KeyboardButton(text="Неизвестно")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer("8️⃣ Является ли пациентом Сабо-Дармон?", reply_markup=keyboard)
    await state.set_state(QuestionnaireStates.Q8_SaboPatient)


@router.message(StateFilter(QuestionnaireStates.Q8_SaboPatient))
async def questionnaire_is_sabodarmon(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    if answer not in ["Да", "Нет", "Неизвестно"]:
        await message.answer("❌ Пожалуйста, выберите один из предложенных вариантов.")
        return

    await state.update_data(q8_is_sabodarmon=answer)

    source_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Telegram"), KeyboardButton(text="Instagram")],
            [KeyboardButton(text="Клиника"), KeyboardButton(text="Знакомые")],
            [KeyboardButton(text="Другое")]
        ],
        resize_keyboard=True, 
        one_time_keyboard=True
    )

    await message.answer("9️⃣ Откуда вы узнали о программе?", reply_markup=source_kb)
    await state.set_state(QuestionnaireStates.Q9_HowFound)


@router.message(StateFilter(QuestionnaireStates.Q9_HowFound))
async def questionnaire_source_info(message: types.Message, state: FSMContext):
    source = message.text.strip()
    valid = ["Telegram", "Instagram", "Клиника", "Знакомые", "Другое"]
    if source not in valid:
        await message.answer("❌ Пожалуйста, выберите один из предложенных вариантов.")
        return

    await state.update_data(q9_source_info=source)

    diagnosis_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]
        ],
        resize_keyboard=True, 
        one_time_keyboard=True
    )

    await message.answer("🔟 Есть ли установленный диагноз?", reply_markup=diagnosis_kb)
    await state.set_state(QuestionnaireStates.Q10_HasDiagnosis)


@router.message(StateFilter(QuestionnaireStates.Q10_HasDiagnosis))
async def questionnaire_has_diagnosis(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    if answer not in ["✅ Да", "❌ Нет"]:
        await message.answer("❌ Выберите один из предложенных вариантов.")
        return

    await state.update_data(q10_has_diagnosis=answer)

    if answer == "✅ Да":
        await message.answer("📝 Укажите диагноз пациента:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(QuestionnaireStates.Q11_DiagnosisText)
    else:
        await message.answer("📎 Прикрепление файла не требуется.\nПереходим к следующему вопросу...", reply_markup=ReplyKeyboardRemove())
        await state.set_state(QuestionnaireStates.Q13_Complaint)
        await message.answer("🔔 Введите кратко жалобу / причину обращения:")


@router.message(StateFilter(QuestionnaireStates.Q11_DiagnosisText))
async def questionnaire_diagnosis_text(message: types.Message, state: FSMContext):
    await state.update_data(q11_diagnosis_text=message.text)

    await message.answer("📎 Прикрепите фото/скан диагноза или эпикриза (по желанию).")
    await state.set_state(QuestionnaireStates.Q12_DiagnosisFile)


@router.message(F.content_type == types.ContentType.DOCUMENT, StateFilter(QuestionnaireStates.Q12_DiagnosisFile))
@router.message(F.content_type == types.ContentType.PHOTO, StateFilter(QuestionnaireStates.Q12_DiagnosisFile))
async def questionnaire_diagnosis_file(message: types.Message, state: FSMContext):
    file_id = message.document.file_id if message.document else message.photo[-1].file_id
    await state.update_data(q12_diagnosis_file_id=file_id)

    await message.answer("✅ Диагноз прикреплён!\n\n🔔 Теперь укажите кратко жалобу / причину обращения:")
    await state.set_state(QuestionnaireStates.Q13_Complaint)


@router.message(StateFilter(QuestionnaireStates.Q13_Complaint))
async def questionnaire_complaint(message: types.Message, state: FSMContext):
    await state.update_data(q13_complaint=message.text)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Боль"), KeyboardButton(text="Нарушение сна")],
            [KeyboardButton(text="Невозможность работать"), KeyboardButton(text="Ограничение в передвижении")],
            [KeyboardButton(text="Другое")]
        ],
        resize_keyboard=True, 
        one_time_keyboard=True
    )

    await message.answer("1️⃣4️⃣ Что доставляет вам наибольшие неудобства от текущей болезни?", reply_markup=kb)
    await state.set_state(QuestionnaireStates.Q14_MainDiscomfort)


@router.message(StateFilter(QuestionnaireStates.Q14_MainDiscomfort))
async def questionnaire_main_discomfort(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    options = ["Боль", "Нарушение сна", "Невозможность работать", "Ограничение в передвижении", "Другое"]
    if answer not in options:
        await message.answer("❌ Выберите один из предложенных вариантов.")
        return

    if answer == "Другое":
        await message.answer("📝 Уточните, что именно вам мешает:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(QuestionnaireStates.Q14_MainDiscomfortOther)
    else:
        await state.update_data(q14_main_discomfort=answer)
        await proceed_to_q15(message, state)


@router.message(StateFilter(QuestionnaireStates.Q14_MainDiscomfortOther))
async def questionnaire_main_discomfort_other(message: types.Message, state: FSMContext):
    await state.update_data(q14_main_discomfort=f"Другое: {message.text}")
    await proceed_to_q15(message, state)


async def proceed_to_q15(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="☑️ Смогу работать / учиться"), KeyboardButton(text="☑️ Самообслуживание")],
            [KeyboardButton(text="☑️ Уменьшится боль"), KeyboardButton(text="☑️ Снижение риска осложнений")],
            [KeyboardButton(text="☑️ Улучшится сон / энергия"), KeyboardButton(text="☑️ Другое")],
            [KeyboardButton(text="✅ Готово")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "1️⃣5️⃣ Что изменится после лечения?\n\n"
        "Выберите всё, что подходит, по одному пункту. Когда закончите — нажмите ✅ Готово.",
        reply_markup=kb
    )
    await state.update_data(q15_improvements=[])
    await state.set_state(QuestionnaireStates.Q15_ImprovementsAfterTreatment)


@router.message(StateFilter(QuestionnaireStates.Q15_ImprovementsAfterTreatment))
async def questionnaire_improvements(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "✅ Готово":
        data = await state.get_data()
        selected = data.get("q15_improvements", [])
        if not selected:
            await message.answer("❗ Выберите хотя бы один пункт.")
            return
        await proceed_to_q16(message, state)
        return

    valid_options = [
        "☑️ Смогу работать / учиться", "☑️ Самообслуживание",
        "☑️ Уменьшится боль", "☑️ Снижение риска осложнений",
        "☑️ Улучшится сон / энергия", "☑️ Другое"
    ]
    if text not in valid_options:
        await message.answer("❌ Пожалуйста, выберите вариант из предложенных.")
        return

    data = await state.get_data()
    selected = data.get("q15_improvements", [])
    if text in selected:
        await message.answer("⚠️ Этот пункт уже выбран.")
    else:
        selected.append(text)
        await state.update_data(q15_improvements=selected)
        await message.answer(f"✅ Добавлено: {text}")


async def proceed_to_q16(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="☑️ Ухудшение состояния"), KeyboardButton(text="☑️ Потеря трудоспособности")],
            [KeyboardButton(text="☑️ Риск инвалидности"), KeyboardButton(text="☑️ Неизвестно")],
            [KeyboardButton(text="✅ Завершить выбор")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "1️⃣6️⃣ Что будет, если не лечиться?\n\n"
        "Выберите всё, что подходит, по одному пункту. Когда закончите — нажмите ✅ Завершить выбор.",
        reply_markup=kb
    )
    await state.update_data(q16_consequences=[])
    await state.set_state(QuestionnaireStates.Q16_WithoutTreatmentConsequences)


@router.message(StateFilter(QuestionnaireStates.Q16_WithoutTreatmentConsequences))
async def questionnaire_consequences(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "✅ Завершить выбор":
        data = await state.get_data()
        selected = data.get("q16_consequences", [])
        if not selected:
            await message.answer("❗ Выберите хотя бы один пункт.")
            return
        await message.answer("✅ Спасибо! Переходим к следующим вопросам...", reply_markup=ReplyKeyboardRemove())
        await proceed_to_q17(message, state)
        return

    valid_options = [
        "☑️ Ухудшение состояния", "☑️ Потеря трудоспособности",
        "☑️ Риск инвалидности", "☑️ Неизвестно"
    ]
    if text not in valid_options:
        await message.answer("❌ Пожалуйста, выберите вариант из предложенных.")
        return

    data = await state.get_data()
    selected = data.get("q16_consequences", [])
    if text in selected:
        await message.answer("⚠️ Этот пункт уже выбран.")
    else:
        selected.append(text)
        await state.update_data(q16_consequences=selected)
        await message.answer(f"✅ Добавлено: {text}")


async def proceed_to_q17(message: types.Message, state: FSMContext):
    options = ["☑️ Да, есть", "☑️ Нет, но можем взять", "☑️ Нет"]
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=option)] for option in options],
        resize_keyboard=True, 
        one_time_keyboard=True
    )
    await message.answer("📄 Есть ли подтверждение нуждаемости от махалли или других органов?", reply_markup=kb)
    await state.set_state(QuestionnaireStates.Q17_NeedConfirmationDocs)


@router.message(StateFilter(QuestionnaireStates.Q17_NeedConfirmationDocs))
async def questionnaire_need_docs(message: types.Message, state: FSMContext):
    options = ["☑️ Да, есть", "☑️ Нет, но можем взять", "☑️ Нет"]
    if message.text not in options:
        await proceed_to_q17(message, state)
        return

    await state.update_data(q17_need_confirmation=message.text)
    await message.answer("📎 Прикрепите документ: справку о нуждаемости, 'темир дафтар' и т.п. (фото или PDF).", reply_markup=ReplyKeyboardRemove())
    await state.set_state(QuestionnaireStates.Q17_ConfirmationFile)


@router.message(F.content_type == types.ContentType.DOCUMENT, StateFilter(QuestionnaireStates.Q17_ConfirmationFile))
async def questionnaire_confirm_doc(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    await state.update_data(q17_confirmation_file=file_id)

    # Переход к следующему шагу
    await message.answer("✅ Документ получен.\n\n📊 Укажите средний доход вашей семьи в месяц:")
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="До 5 млн"), KeyboardButton(text="5–7 млн")],
            [KeyboardButton(text="7–10 млн"), KeyboardButton(text="10+ млн")]
        ],
        resize_keyboard=True, 
        one_time_keyboard=True
    )
    await message.answer("Выберите:", reply_markup=kb)
    await state.set_state(QuestionnaireStates.Q18_AvgIncome)


@router.message(StateFilter(QuestionnaireStates.Q18_AvgIncome))
async def questionnaire_avg_income(message: types.Message, state: FSMContext):
    options = ["До 5 млн", "5–7 млн", "7–10 млн", "10+ млн"]
    if message.text not in options:
        await message.answer("❌ Выберите один из вариантов.")
        return

    await state.update_data(q18_avg_income=message.text)
    await message.answer("📎 Прикрепите подтверждающий документ (справка о доходах, выписка и т.п.).", reply_markup=ReplyKeyboardRemove())
    await state.set_state(QuestionnaireStates.Q18_IncomeDoc)


@router.message(F.content_type == types.ContentType.DOCUMENT, StateFilter(QuestionnaireStates.Q18_IncomeDoc))
async def questionnaire_income_doc(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    await state.update_data(q18_income_doc=file_id)

    await message.answer("👶 Сколько несовершеннолетних детей в семье?")
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="0"), KeyboardButton(text="1"), KeyboardButton(text="2")],
            [KeyboardButton(text="3"), KeyboardButton(text="4"), KeyboardButton(text="5+")]
        ],
        resize_keyboard=True, 
        one_time_keyboard=True
    )
    await message.answer("Выберите число:", reply_markup=kb)
    await state.set_state(QuestionnaireStates.Q19_ChildrenCount)


@router.message(StateFilter(QuestionnaireStates.Q19_ChildrenCount))
async def questionnaire_children_count(message: types.Message, state: FSMContext):
    if message.text not in ["0", "1", "2", "3", "4", "5+"]:
        await message.answer("❌ Пожалуйста, выберите количество из предложенных.")
        return

    await state.update_data(q19_children_count=message.text)
    if message.text != "0":
        await message.answer("📎 Прикрепите метрику каждого ребёнка (можно несколько файлов).", reply_markup=ReplyKeyboardRemove())
        await state.set_state(QuestionnaireStates.Q19_ChildrenDocs)
    else:
        await proceed_to_q20(message, state)


@router.message(F.content_type == types.ContentType.DOCUMENT, StateFilter(QuestionnaireStates.Q19_ChildrenDocs))
async def questionnaire_children_docs(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    data = await state.get_data()
    children_docs = data.get("q19_children_docs", [])
    children_docs.append(file_id)
    await state.update_data(q19_children_docs=children_docs)

    await message.answer("✅ Метрика получена.")
    await proceed_to_q20(message, state)


async def proceed_to_q20(message: types.Message, state: FSMContext):
    options = ["☑️ Собственное", "☑️ Аренда", "☑️ У родственников"]
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=option)] for option in options],
        resize_keyboard=True, 
        one_time_keyboard=True
    )

    await message.answer("🏠 Какой у вас тип жилья?", reply_markup=kb)
    await state.set_state(QuestionnaireStates.Q20_HousingType)


@router.message(StateFilter(QuestionnaireStates.Q20_HousingType))
async def questionnaire_housing_type(message: types.Message, state: FSMContext):
    options = ["☑️ Собственное", "☑️ Аренда", "☑️ У родственников"]
    if message.text not in options:
        await proceed_to_q20(message, state)
        return

    await state.update_data(q20_housing_type=message.text)

    if message.text == "☑️ Аренда":
        await message.answer("📎 Прикрепите договор аренды или подтверждающий документ.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(QuestionnaireStates.Q20_HousingDoc)
    else:
        await proceed_to_q21(message, state)


@router.message(F.content_type == types.ContentType.DOCUMENT, StateFilter(QuestionnaireStates.Q20_HousingDoc))
async def questionnaire_housing_doc(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    await state.update_data(q20_housing_doc=file_id)

    await message.answer("✅ Документ по жилью получен.")
    await proceed_to_q21(message, state)


async def proceed_to_q21(message: types.Message, state: FSMContext):
    await message.answer("💰 До какой суммы вы можете оплатить лечение? (в сумах)", reply_markup=ReplyKeyboardRemove())
    await state.set_state(QuestionnaireStates.Q21_WhoWorksInFamily)


@router.message(StateFilter(QuestionnaireStates.Q20_HousingDoc))
async def questionnaire_contribution(message: types.Message, state: FSMContext):
    amount = message.text.strip().replace(" ", "")
    if not amount.isdigit():
        await message.answer("❌ Введите только сумму в числовом формате, без текста.")
        return

    await state.update_data(q21_contribution=amount)
    await message.answer(
        "📎 Прикрепите любой другой документ, подтверждающий ваши обстоятельства (по желанию).\n"
        "Вы можете пропустить этот шаг, отправив любое сообщение без файла."
    )
    await state.set_state(QuestionnaireStates.Q22_AdditionalFile)

@router.message(F.content_type == types.ContentType.DOCUMENT, StateFilter(QuestionnaireStates.Q22_AdditionalFile))
async def questionnaire_additional_file(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    await state.update_data(q22_additional_file=file_id)

    await message.answer("📝 Есть ли у вас другие важные обстоятельства, которые помогут С-Д принять правильное решение?")
    await state.set_state(QuestionnaireStates.Q23_FinalComment)


@router.message(StateFilter(QuestionnaireStates.Q22_AdditionalFile))
async def skip_additional_file(message: types.Message, state: FSMContext):
    await state.update_data(q22_additional_file=None)
    await message.answer("📝 Есть ли у вас другие важные обстоятельства, которые помогут С-Д принять правильное решение?")
    await state.set_state(QuestionnaireStates.Q23_FinalComment)

@router.message(StateFilter(QuestionnaireStates.Q23_FinalComment))
async def questionnaire_final_comment(message: Message, state: FSMContext):
    await state.update_data(q23_final_comment=message.text)

    data = await state.get_data()
    summary = (
        "✅ Анкета завершена!\n\n"
        f"👤 ФИО: {data.get('q1_full_name')}\n"
        f"📅 Дата рождения: {data.get('q2_birth_date')}\n"
        f"🧑 Пол: {data.get('q3_gender')}\n"
        f"📞 Телефон: {data.get('q4_phone_number')}\n"
        f"📲 Telegram: {data.get('q5_telegram_username')}\n"
        f"🏠 Жильё: {data.get('q20_housing_type')}\n"
        f"💰 Оплата: {data.get('q21_contribution')} сум\n"
        f"📄 Комментарий: {data.get('q23_final_comment')}\n\n"
        "Данные сохранены. Мы свяжемся с вами после проверки!"
    )

    await message.answer(summary)
    await state.clear()