from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Message
from aiogram3_calendar.simple_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram.filters import StateFilter
from datetime import datetime

from robot.utils.google_drive import save_full_questionnaire_to_drive, create_folder, PARENT_FOLDER_ID
from robot.utils.financial_score_calculator import calculate_final_conclusion, format_conclusion_message
from robot.utils.question_labels import get_question_label, get_keyboard_for, QUESTION_FLOW, get_multi_choice_keyboard
import re
from robot.models import Patient, BotUser
from asgiref.sync import sync_to_async
from aiogram import Router
from aiogram.filters import StateFilter
from robot.states import QuestionnaireStates
from robot.utils.validators import is_pdf, is_allowed_file


router = Router()

REGIONS = [
    "Андижанская область — Андижан",
    "Бухарская область — Бухара",
    "Джизакская область — Джизак",
    "Кашкадарьинская область — Карши",
    "Навоийская область — Навоий",
    "Наманганская область — Наманган",
    "Самаркандская область — Самарканд",
    "Сурхандарьинская область — Термез",
    "Сырдарьинская область — Гулистан",
    "Ташкентская область — Нурафшан",
    "Ферганская область — Фергана",
    "Хорезмская область — Ургенч",
    "Республика Каракалпакстан — Нукус",
    "г. Ташкент — Ташкент",
    "Другое"
]


STATE_ORDER = [
    "ConfirmRules",
    "Q1_FullName", 
    "Q2_BirthDate",
    "Q3_Gender",
    "Q4_PhoneNumber", 
    "Q5_TelegramUsername",
    "Q6_Region",
    "Q7_WhoApplies",
    "Q8_SaboPatient",
    "Q9_HowFound",
    "Q10_HasDiagnosis",
    "Q11_DiagnosisText",
    "Q12_DiagnosisFile", 
    "Q13_Complaint",
    "Q14_MainDiscomfort",
    "Q14_MainDiscomfortOther",
    "Q15_ImprovementsAfterTreatment",
    "Q16_WithoutTreatmentConsequences", 
    "Q17_NeedConfirmationDocs",
    "Q17_ConfirmationFile",
    "Q18_AvgIncome",
    "Q18_IncomeDoc",
    "Q19_ChildrenCount",
    "Q19_ChildrenDocs",
    "Q21_FamilyWork",
    "Q22_HousingType",
    "Q22_HousingDoc",
    # "Q23_Contribution",
    # "Q23_ContributionConfirm",
    "Q24_AdditionalFile",
    "Q25_FinalComment"
]

def get_previous_state(current_state: str, user_data: dict = None) -> str:
    """Получить предыдущее состояние с учетом логики пропуска"""
    try:
        current_index = STATE_ORDER.index(current_state)
        if current_index <= 1:  # ConfirmRules или Q1_FullName
            return None
            
        # Логика для состояний с условными переходами
        if current_state == "Q13_Complaint":
            # Если диагноза нет, возвращаемся к Q10_HasDiagnosis
            if user_data and user_data.get("q10_has_diagnosis") == "❌ Нет":
                return "Q10_HasDiagnosis"
            else:
                return "Q12_DiagnosisFile"
                
        elif current_state == "Q17_ConfirmationFile":
            return "Q17_NeedConfirmationDocs"
            
        elif current_state == "Q18_IncomeDoc":
            return "Q18_AvgIncome"
            
        elif current_state == "Q19_ChildrenDocs":
            return "Q19_ChildrenCount"
            
        elif current_state == "Q21_FamilyWork":
            # Если детей нет, возвращаемся к Q19_ChildrenCount
            if user_data and user_data.get("q19_children_count") == "0":
                return "Q19_ChildrenCount"
            else:
                return "Q19_ChildrenDocs"
                
        elif current_state == "Q22_HousingDoc":
            return "Q22_HousingType"
            
        # elif current_state == "Q23_ContributionConfirm":
        #     return "Q23_Contribution"
        elif current_state == "Q24_AdditionalFile":
            return "Q22_HousingType"
        elif current_state == "Q25_FinalComment":
            return "Q24_AdditionalFile"
            
        return STATE_ORDER[current_index - 1]
        
    except ValueError:
        return None

async def handle_back_button(message: types.Message, state: FSMContext):
    """Обработка нажатия кнопки Назад"""
    current_state = await state.get_state()
    user_data = await state.get_data()
    
    # Получаем имя состояния без префикса
    state_name = current_state.split(":")[-1] if ":" in current_state else current_state
    
    previous_state = get_previous_state(state_name, user_data)
    
    if not previous_state:
        await message.answer("❌ Нельзя вернуться назад с первого вопроса.")
        return False
        
    # Очищаем данные текущего вопроса при возврате назад
    clear_current_data(state_name, user_data)
    await state.update_data(**user_data)
    
    # Переходим к предыдущему состоянию
    await navigate_to_state(previous_state, message, state)
    return True

def clear_current_data(state_name: str, user_data: dict):
    """Очистка данных текущего состояния при возврате"""
    state_to_data_map = {
        "Q2_BirthDate": "q2_birth_date",
        "Q3_Gender": "q3_gender", 
        "Q4_PhoneNumber": "q4_phone_number",
        "Q5_TelegramUsername": "q5_telegram_username",
        "Q6_Region": "q6_region",
        "Q7_WhoApplies": "q7_who_applies",
        "Q8_SaboPatient": "q8_is_sabodarmon",
        "Q9_HowFound": "q9_source_info",
        "Q10_HasDiagnosis": "q10_has_diagnosis",
        "Q11_DiagnosisText": "q11_diagnosis_text",
        "Q12_DiagnosisFile": "q12_diagnosis_file_id",
        "Q13_Complaint": "q13_complaint",
        "Q14_MainDiscomfort": "q14_main_discomfort",
        "Q15_ImprovementsAfterTreatment": "q15_improvements",
        "Q16_WithoutTreatmentConsequences": "q16_consequences",
        "Q17_NeedConfirmationDocs": "q17_need_confirmation",
        "Q17_ConfirmationFile": "q17_confirmation_file",
        "Q18_AvgIncome": "q18_avg_income",
        "Q18_IncomeDoc": "q18_income_doc",
        "Q19_ChildrenCount": "q19_children_count",
        "Q19_ChildrenDocs": "q19_children_docs",
        "Q21_FamilyWork": "q21_family_work",
        "Q22_HousingType": "q22_housing_type",
        "Q22_HousingDoc": "q22_housing_doc",
        # "Q23_Contribution": "q23_contribution",
        "Q24_AdditionalFile": "q24_additional_file",
        "Q25_FinalComment": "q25_final_comment"
    }
    
    data_key = state_to_data_map.get(state_name)
    if data_key and data_key in user_data:
        del user_data[data_key]
    if state_name == "Q6_Region" and "q6_manual_region" in user_data:
        del user_data["q6_manual_region"]



async def navigate_to_state(state_name: str, message: types.Message, state: FSMContext):
    """Навигация к определенному состоянию"""
    user_data = await state.get_data()
    
    if state_name == "Q2_BirthDate":
        label = get_question_label("Q2_BirthDate")
        await message.answer(label, reply_markup=await SimpleCalendar().start_calendar())
        await state.set_state(QuestionnaireStates.Q2_BirthDate)
        
    elif state_name == "Q4_PhoneNumber":
        label = get_question_label("Q4_PhoneNumber")
        phone_button = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)], [KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(label, reply_markup=phone_button)
        await state.set_state(QuestionnaireStates.Q4_PhoneNumber)
        
    elif state_name == "Q5_TelegramUsername":
        label = get_question_label("Q5_TelegramUsername")
        username_button = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="👤 Отправить Telegram username")], [KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(label, reply_markup=username_button)
        await state.set_state(QuestionnaireStates.Q5_TelegramUsername)
    
    elif state_name == "Q6_Region":
        label = get_question_label("Q6_Region")
        username_button = get_region_keyboard()
        await message.answer(label, reply_markup=username_button)
        await state.set_state(QuestionnaireStates.Q6_Region)
        
    elif state_name == "Q11_DiagnosisText":
        await message.answer(get_question_label("Q11_DiagnosisText"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        await state.set_state(QuestionnaireStates.Q11_DiagnosisText)
        
    elif state_name == "Q12_DiagnosisFile":
        await message.answer(get_question_label("Q12_DiagnosisFile"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        await state.set_state(QuestionnaireStates.Q12_DiagnosisFile)
        
    elif state_name == "Q13_Complaint":
        await message.answer(get_question_label("Q13_Complaint"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        await state.set_state(QuestionnaireStates.Q13_Complaint)
        
    elif state_name == "Q14_MainDiscomfortOther":
        await message.answer("📝 Уточните, что именно вам мешает:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        await state.set_state(QuestionnaireStates.Q14_MainDiscomfortOther)
        
    elif state_name == "Q15_ImprovementsAfterTreatment":
        await state.update_data(q15_improvements=[])
        await proceed_to_q15(message, state)
        
    elif state_name == "Q16_WithoutTreatmentConsequences":
        await state.update_data(q16_consequences=[])
        await proceed_to_q16(message, state)
        
    elif state_name == "Q17_ConfirmationFile":
        await message.answer(get_question_label("Q17_ConfirmationFile"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        await state.set_state(QuestionnaireStates.Q17_ConfirmationFile)
        
    elif state_name == "Q18_IncomeDoc":
        await message.answer(get_question_label("Q18_IncomeDoc"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        await state.set_state(QuestionnaireStates.Q18_IncomeDoc)
        
    elif state_name == "Q19_ChildrenDocs":
        await state.update_data(q19_children_docs=[])
        await message.answer(get_question_label("Q19_ChildrenDocs"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Завершить загрузку")], [KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        await state.set_state(QuestionnaireStates.Q19_ChildrenDocs)
        
    elif state_name == "Q22_HousingDoc":
        await message.answer(get_question_label("Q22_HousingDoc"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        await state.set_state(QuestionnaireStates.Q22_HousingDoc)
        
    # elif state_name == "Q23_Contribution":
    #     await message.answer(get_question_label("Q23_Contribution"), reply_markup=ReplyKeyboardMarkup(
    #         keyboard=[[KeyboardButton(text="⬅️ Назад")]],
    #         resize_keyboard=True
    #     ))
    #     await state.set_state(QuestionnaireStates.Q23_Contribution)
        
    elif state_name == "Q24_AdditionalFile":
        await message.answer(get_question_label("Q24_AdditionalFile"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        await state.set_state(QuestionnaireStates.Q24_AdditionalFile)
        
    elif state_name == "Q25_FinalComment":
        await message.answer(get_question_label("Q25_FinalComment"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        await state.set_state(QuestionnaireStates.Q25_FinalComment)
        
    else:
        # Для остальных состояний используем стандартную функцию
        await proceed_with_keyboard(state_name, message, state)

@router.message(F.text == "⬅️ Назад")
async def handle_back_navigation(message: types.Message, state: FSMContext):
    await handle_back_button(message, state)



def get_back_only_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )



def get_region_keyboard():
    keyboard = []
    for i in range(0, len(REGIONS), 2):
        row = [KeyboardButton(text=REGIONS[i])]
        if i + 1 < len(REGIONS):
            row.append(KeyboardButton(text=REGIONS[i + 1]))
        keyboard.append(row)

    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

@router.message(
    StateFilter(
        QuestionnaireStates.Q12_DiagnosisFile,
        QuestionnaireStates.Q17_ConfirmationFile,
        QuestionnaireStates.Q18_IncomeDoc,
        QuestionnaireStates.Q22_HousingDoc,
    ),
    ~F.content_type.in_({types.ContentType.DOCUMENT, types.ContentType.PHOTO})
)
async def invalid_file_input(message: types.Message):
    await message.answer("❌ Пожалуйста, прикрепите файл как PDF-документ или фото, а не отправляйте текст, аудио или голосовое.")

@router.message(StateFilter(QuestionnaireStates.Q1_FullName, QuestionnaireStates.Q11_DiagnosisText,QuestionnaireStates.Q13_Complaint, QuestionnaireStates.Q25_FinalComment),
                ~(F.content_type == types.ContentType.TEXT))
async def invalid_diagnosis_text_input(message: types.Message):
    await message.answer("❌ Пожалуйста, введите диагноз ТЕКСТОМ, а не отправляйте файл, голосовое или фото.")

async def proceed_with_keyboard(state_name: str, message: types.Message, state: FSMContext):
    label = get_question_label(state_name)
    kb = get_keyboard_for(state_name)
    if state_name == "Q25_FinalComment":
        await message.answer(
            label,
            reply_markup=kb if kb else get_back_only_keyboard()
        )
    else:
        await message.answer(label, reply_markup=kb if kb else ReplyKeyboardRemove())
    await state.set_state(getattr(QuestionnaireStates, state_name))


@router.message(StateFilter(QuestionnaireStates.ConfirmRules))
async def confirm_rules(message: types.Message, state: FSMContext):
    if message.text == "✅ Я согласен с условиями":
        label = get_question_label("Q1_FullName")
        await message.answer("Анкета началась 📝\n\n" + label, reply_markup=ReplyKeyboardRemove())
        await state.set_state(QuestionnaireStates.Q1_FullName)
    else:
        await message.answer("⚠️ Вы должны подтвердить условия участия для продолжения.")

@router.message(
    StateFilter(QuestionnaireStates.Q1_FullName),
    F.content_type == types.ContentType.TEXT
)
async def questionnaire_full_name(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await message.answer("⛔ Вы на первом шаге. Назад невозможно.")
        return
    
    await state.update_data(q1_full_name=message.text)

    label = get_question_label("Q2_BirthDate")
    
    await message.answer(label, reply_markup=get_back_only_keyboard())
    
    calendar = await SimpleCalendar().start_calendar()
    await message.answer("📅 Выберите дату рождения ниже:", reply_markup=calendar)

    await state.set_state(QuestionnaireStates.Q2_BirthDate)



@router.callback_query(SimpleCalendarCallback.filter(), StateFilter(QuestionnaireStates.Q2_BirthDate))
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    try:
        selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)

        if selected:
            await state.update_data(q2_birth_date=date.strftime("%d.%m.%Y"))

            label = get_question_label("Q3_Gender")
            keyboard = get_keyboard_for("Q3_Gender")
            await callback_query.message.answer(label, reply_markup=keyboard)
            await state.set_state(QuestionnaireStates.Q3_Gender)
        else:
            await callback_query.answer("📅 Пожалуйста, выберите дату, а не переходите по месяцам", show_alert=False)

    except Exception as e:
        print(f"❌ Error in process_simple_calendar: {e}")
        await callback_query.message.answer("⚠️ Ошибка при выборе даты. Попробуйте ещё раз.")
        await callback_query.answer()

        


@router.message(StateFilter(QuestionnaireStates.Q3_Gender))
async def questionnaire_gender(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await handle_back_button(message, state)
        return
        
    gender = message.text.lower()
    if gender not in ["мужской", "женский"]:
        await message.answer("❌ Пожалуйста, выберите один из вариантов: Мужской или Женский.")
        return

    await state.update_data(q3_gender=gender.capitalize())

    label = get_question_label("Q4_PhoneNumber")
    phone_button = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер", request_contact=True)], 
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(label, reply_markup=phone_button)
    await state.set_state(QuestionnaireStates.Q4_PhoneNumber)



@router.message(StateFilter(QuestionnaireStates.Q4_PhoneNumber), F.content_type == types.ContentType.CONTACT)
async def questionnaire_phone_contact(message: types.Message, state: FSMContext):
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("❌ Пожалуйста, отправьте СВОЙ номер через кнопку: '📱 Отправить номер'.")
        return

    await state.update_data(q4_phone_number=contact.phone_number)

    label = get_question_label("Q5_TelegramUsername")
    username_button = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Отправить Telegram username")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(label, reply_markup=username_button)
    await state.set_state(QuestionnaireStates.Q5_TelegramUsername)


@router.message(StateFilter(QuestionnaireStates.Q5_TelegramUsername))
async def questionnaire_username(message: types.Message, state: FSMContext):
    if message.text == "👤 Отправить Telegram username":
        tg_username = message.from_user.username
        if tg_username:
            username = f"@{tg_username}"
            await state.update_data(q5_telegram_username=username)
            await message.answer(f"✅ Ваш Telegram username: {username}")
        else:
            await message.answer("❗ У вас не установлен Telegram username.\nПожалуйста, введите его вручную (например: @yourname):", reply_markup=ReplyKeyboardRemove())
            return
    else:
        username = message.text.strip()
        if not re.match(r"^@[\w\d_]{5,}$", username):
            await message.answer("❌ Введите корректный Telegram username, начинающийся с @.")
            return
        await state.update_data(q5_telegram_username=username)

    label = get_question_label("Q6_Region")
    await message.answer(label, reply_markup=get_region_keyboard())
    await state.set_state(QuestionnaireStates.Q6_Region)


@router.message(StateFilter(QuestionnaireStates.Q6_Region))
async def questionnaire_region(message: types.Message, state: FSMContext):
    region_input = message.text.strip()
    data = await state.get_data()

    # Шаг 1: если ожидаем ручной ввод после "Другое"
    if data.get("q6_manual_region"):
        await state.update_data(q6_region=region_input)
        await state.update_data(q6_manual_region=False)  # сброс флага
        await message.answer("✅ Регион сохранён.", reply_markup=ReplyKeyboardRemove())
        label = get_question_label("Q7_WhoApplies")
        keyboard = get_keyboard_for("Q7_WhoApplies")
        await message.answer(label, reply_markup=keyboard)
        await state.set_state(QuestionnaireStates.Q7_WhoApplies)
        return

    # Шаг 2: пользователь нажал "Другое"
    if region_input == "Другое":
        await state.update_data(q6_manual_region=True)  # включаем флаг ручного ввода
        await message.answer(
            "✏️ Пожалуйста, введите регион и город вручную (например: 'Хатирчинский район, Навоий').",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Шаг 3: проверка на валидный регион
    if region_input not in REGIONS:
        await message.answer("❌ Пожалуйста, выберите вариант из списка или нажмите «Другое» для ручного ввода.")
        return

    # Шаг 4: пользователь выбрал из предложенного списка
    await state.update_data(q6_region=region_input)
    await message.answer("✅ Регион сохранён.", reply_markup=ReplyKeyboardRemove())
    label = get_question_label("Q7_WhoApplies")
    keyboard = get_keyboard_for("Q7_WhoApplies")
    await message.answer(label, reply_markup=keyboard)
    await state.set_state(QuestionnaireStates.Q7_WhoApplies)



@router.message(StateFilter(QuestionnaireStates.Q7_WhoApplies))
async def questionnaire_who_applies(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    if answer not in QUESTION_FLOW["Q7_WhoApplies"]["options"]:
        await message.answer("❌ Пожалуйста, выберите один из предложенных вариантов.")
        return

    await state.update_data(q7_who_applies=answer)

    next_state = QuestionnaireStates.Q8_SaboPatient
    await message.answer(
        get_question_label("Q8_SaboPatient"),
        reply_markup=get_keyboard_for("Q8_SaboPatient")
    )
    await state.set_state(next_state)


@router.message(StateFilter(QuestionnaireStates.Q8_SaboPatient))
async def questionnaire_is_sabodarmon(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    if answer not in QUESTION_FLOW["Q8_SaboPatient"]["options"]:
        await message.answer("❌ Пожалуйста, выберите один из предложенных вариантов.")
        return

    await state.update_data(q8_is_sabodarmon=answer)

    next_state = QuestionnaireStates.Q9_HowFound
    await message.answer(
        get_question_label("Q9_HowFound"),
        reply_markup=get_keyboard_for("Q9_HowFound")
    )
    await state.set_state(next_state)



@router.message(StateFilter(QuestionnaireStates.Q9_HowFound))
async def questionnaire_source_info(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    if answer not in QUESTION_FLOW["Q9_HowFound"]["options"]:
        await message.answer("❌ Пожалуйста, выберите один из предложенных вариантов.")
        return

    await state.update_data(q9_source_info=answer)

    next_state = QuestionnaireStates.Q10_HasDiagnosis
    await message.answer(
        get_question_label("Q10_HasDiagnosis"),
        reply_markup=get_keyboard_for("Q10_HasDiagnosis")
    )
    await state.set_state(next_state)




@router.message(StateFilter(QuestionnaireStates.Q10_HasDiagnosis))
async def questionnaire_has_diagnosis(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    if answer not in QUESTION_FLOW["Q10_HasDiagnosis"]["options"]:
        await message.answer("❌ Выберите один из предложенных вариантов.")
        return

    await state.update_data(q10_has_diagnosis=answer)

    if answer == "✅ Да":
        await message.answer(get_question_label("Q11_DiagnosisText"), reply_markup=get_back_only_keyboard())
        await state.set_state(QuestionnaireStates.Q11_DiagnosisText)
    else:
        await message.answer("📎 Прикрепление файла не требуется.", reply_markup=ReplyKeyboardRemove())
        await message.answer(get_question_label("Q13_Complaint"))
        await state.set_state(QuestionnaireStates.Q13_Complaint)

@router.message(StateFilter(QuestionnaireStates.Q11_DiagnosisText), F.content_type == types.ContentType.TEXT)
async def questionnaire_diagnosis_text(message: types.Message, state: FSMContext):
    await state.update_data(q11_diagnosis_text=message.text.strip())

    await message.answer(get_question_label("Q12_DiagnosisFile"), reply_markup=get_back_only_keyboard())
    await state.set_state(QuestionnaireStates.Q12_DiagnosisFile)


@router.message(StateFilter(QuestionnaireStates.Q11_DiagnosisText))
async def invalid_diagnosis_text_input(message: types.Message):
    await message.answer("❌ Пожалуйста, введите диагноз ТЕКСТОМ, а не отправляйте голосовое или файл.")

@router.message(F.content_type.in_({types.ContentType.DOCUMENT, types.ContentType.PHOTO}), StateFilter(QuestionnaireStates.Q12_DiagnosisFile))
async def questionnaire_diagnosis_file(message: types.Message, state: FSMContext):
    if not is_allowed_file(message):
        await message.answer("❌ Пожалуйста, прикрепите PDF или изображение (фото диагноза).")
        return

    file_id = message.document.file_id if message.document else message.photo[-1].file_id
    await state.update_data(q12_diagnosis_file_id=file_id)

    await message.answer("✅ Диагноз прикреплён!\n\n" + get_question_label("Q13_Complaint"))
    await state.set_state(QuestionnaireStates.Q13_Complaint)


@router.message(StateFilter(QuestionnaireStates.Q13_Complaint), F.content_type == types.ContentType.TEXT)
async def questionnaire_complaint(message: types.Message, state: FSMContext):
    await state.update_data(q13_complaint=message.text)

    label = get_question_label("Q14_MainDiscomfort")
    kb = get_keyboard_for("Q14_MainDiscomfort")

    await message.answer(label, reply_markup=kb)
    await state.set_state(QuestionnaireStates.Q14_MainDiscomfort)


@router.message(StateFilter(QuestionnaireStates.Q14_MainDiscomfort))
async def questionnaire_main_discomfort(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    valid_options = QUESTION_FLOW["Q14_MainDiscomfort"]["options"]

    if answer not in valid_options:
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
    label = get_question_label("Q15_ImprovementsAfterTreatment")
    kb = get_multi_choice_keyboard("Q15_ImprovementsAfterTreatment")

    await message.answer(label, reply_markup=kb)
    await state.update_data(q15_improvements=[])
    await state.set_state(QuestionnaireStates.Q15_ImprovementsAfterTreatment)


@router.message(StateFilter(QuestionnaireStates.Q15_ImprovementsAfterTreatment))
async def questionnaire_improvements(message: types.Message, state: FSMContext):
    text = message.text.strip()
    options = QUESTION_FLOW["Q15_ImprovementsAfterTreatment"]["options"]
    finish = QUESTION_FLOW["Q15_ImprovementsAfterTreatment"]["finish_button"]

    if text == finish:
        selected = (await state.get_data()).get("q15_improvements", [])
        if not selected:
            await message.answer("❗ Выберите хотя бы один пункт.")
            return
        await proceed_to_q16(message, state)
        return

    if text not in options:
        await message.answer("❌ Пожалуйста, выберите вариант из предложенных.")
        return

    selected = (await state.get_data()).get("q15_improvements", [])
    if text in selected:
        await message.answer("⚠️ Этот пункт уже выбран.")
    else:
        selected.append(text)
        await state.update_data(q15_improvements=selected)
        await message.answer(f"✅ Добавлено: {text}")

async def proceed_to_q16(message: types.Message, state: FSMContext):
    label = get_question_label("Q16_WithoutTreatmentConsequences")
    kb = get_multi_choice_keyboard("Q16_WithoutTreatmentConsequences")

    await message.answer(label, reply_markup=kb)
    await state.update_data(q16_consequences=[])
    await state.set_state(QuestionnaireStates.Q16_WithoutTreatmentConsequences)



@router.message(StateFilter(QuestionnaireStates.Q16_WithoutTreatmentConsequences))
async def questionnaire_consequences(message: types.Message, state: FSMContext):
    text = message.text.strip()
    options = QUESTION_FLOW["Q16_WithoutTreatmentConsequences"]["options"]
    finish = QUESTION_FLOW["Q16_WithoutTreatmentConsequences"]["finish_button"]

    if text == finish:
        selected = (await state.get_data()).get("q16_consequences", [])
        if not selected:
            await message.answer("❗ Выберите хотя бы один пункт.")
            return
        await message.answer("✅ Спасибо! Переходим к следующим вопросам...", reply_markup=ReplyKeyboardRemove())
        await proceed_to_q17(message, state)
        return

    if text not in options:
        await message.answer("❌ Пожалуйста, выберите вариант из предложенных.")
        return

    selected = (await state.get_data()).get("q16_consequences", [])
    if text in selected:
        await message.answer("⚠️ Этот пункт уже выбран.")
    else:
        selected.append(text)
        await state.update_data(q16_consequences=selected)
        await message.answer(f"✅ Добавлено: {text}")


async def proceed_to_q17(message: types.Message, state: FSMContext):
    label = get_question_label("Q17_NeedConfirmationDocs")
    kb = get_keyboard_for("Q17_NeedConfirmationDocs")
    await message.answer(label, reply_markup=kb)
    await state.set_state(QuestionnaireStates.Q17_NeedConfirmationDocs)


@router.message(StateFilter(QuestionnaireStates.Q17_NeedConfirmationDocs))
async def questionnaire_need_docs(message: types.Message, state: FSMContext):
    user_choice = message.text.strip()
    options = QUESTION_FLOW["Q17_NeedConfirmationDocs"]["options"]

    if user_choice not in options:
        await message.answer("❌ Пожалуйста, выберите один из предложенных вариантов.")
        await proceed_to_q17(message, state)
        return

    await state.update_data(q17_need_confirmation=user_choice)

    if user_choice == "☑️ Да, есть":
        await message.answer(get_question_label("Q17_ConfirmationFile"), reply_markup=get_back_only_keyboard())
        await state.set_state(QuestionnaireStates.Q17_ConfirmationFile)
    else:
        await proceed_to_q18(message, state)


@router.message(
    F.content_type.in_({types.ContentType.DOCUMENT, types.ContentType.PHOTO}),
    StateFilter(QuestionnaireStates.Q17_ConfirmationFile)
)
async def questionnaire_confirm_doc(message: types.Message, state: FSMContext):
    file_id = message.document.file_id if message.document else message.photo[-1].file_id if message.photo else None

    if not file_id:
        await message.answer("❌ Прикрепите PDF или изображение.")
        return

    await state.update_data(q17_confirmation_file=file_id)
    await message.answer("✅ Документ получен.")
    await proceed_to_q18(message, state)


async def proceed_to_q18(message: types.Message, state: FSMContext):
    label = get_question_label("Q18_AvgIncome")
    kb = get_keyboard_for("Q18_AvgIncome")
    await message.answer(label, reply_markup=kb)
    await state.set_state(QuestionnaireStates.Q18_AvgIncome)



@router.message(StateFilter(QuestionnaireStates.Q18_AvgIncome))
async def questionnaire_avg_income(message: types.Message, state: FSMContext):
    user_choice = message.text.strip()
    options = QUESTION_FLOW["Q18_AvgIncome"]["options"]

    if user_choice not in options:
        await message.answer("❌ Выберите один из предложенных вариантов.")
        return

    await state.update_data(q18_avg_income=user_choice)
    await message.answer(get_question_label("Q18_IncomeDoc"), reply_markup=get_back_only_keyboard())
    await state.set_state(QuestionnaireStates.Q18_IncomeDoc)



@router.message(
    F.content_type.in_({types.ContentType.DOCUMENT, types.ContentType.PHOTO}),
    StateFilter(QuestionnaireStates.Q18_IncomeDoc)
)
async def questionnaire_income_doc(message: types.Message, state: FSMContext):
    file_id = message.document.file_id if message.document else message.photo[-1].file_id if message.photo else None

    if not file_id:
        await message.answer("❌ Прикрепите PDF или изображение документа о доходах.")
        return

    await state.update_data(q18_income_doc=file_id)
    await proceed_to_q19(message, state)

async def proceed_to_q19(message: types.Message, state: FSMContext):
    label = get_question_label("Q19_ChildrenCount")
    kb = get_keyboard_for("Q19_ChildrenCount")
    await message.answer(label, reply_markup=kb)
    await state.set_state(QuestionnaireStates.Q19_ChildrenCount)



@router.message(StateFilter(QuestionnaireStates.Q19_ChildrenCount))
async def questionnaire_children_count(message: types.Message, state: FSMContext):
    choice = message.text.strip()
    if choice not in QUESTION_FLOW["Q19_ChildrenCount"]["options"]:
        await message.answer("❌ Пожалуйста, выберите количество из предложенных.")
        return

    await state.update_data(q19_children_count=choice)

    if choice == "0":
        await proceed_with_keyboard("Q21_FamilyWork", message, state)
    else:
        await state.update_data(q19_children_docs=[])
        await message.answer(get_question_label("Q19_ChildrenDocs"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Завершить загрузку")],
                [KeyboardButton(text="⬅️ Назад")]
                ],
            
            resize_keyboard=True
        ))
        await state.set_state(QuestionnaireStates.Q19_ChildrenDocs)



@router.message(
    F.content_type.in_({types.ContentType.DOCUMENT, types.ContentType.PHOTO}),
    StateFilter(QuestionnaireStates.Q19_ChildrenDocs)
)
async def questionnaire_children_docs(message: types.Message, state: FSMContext):
    file_id = message.document.file_id if message.document else message.photo[-1].file_id

    data = await state.get_data()
    files = data.get("q19_children_docs", [])
    files.append(file_id)
    await state.update_data(q19_children_docs=files)

    await message.answer(f"✅ Метрика получена ({len(files)} файл(ов)).")


@router.message(F.text == "✅ Завершить загрузку", StateFilter(QuestionnaireStates.Q19_ChildrenDocs))
async def finish_children_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    count_raw = data.get("q19_children_count", "0")
    expected = 5 if count_raw == "5+" else int(count_raw)
    uploaded = len(data.get("q19_children_docs", []))

    if uploaded < expected:
        await message.answer(f"❗ Вы указали {expected} детей, но загрузили только {uploaded} файл(ов).")
        return

    await message.answer("✅ Загрузка завершена.", reply_markup=ReplyKeyboardRemove())
    await proceed_with_keyboard("Q21_FamilyWork", message, state)



@router.message(StateFilter(QuestionnaireStates.Q21_FamilyWork))
async def questionnaire_family_work(message: types.Message, state: FSMContext):
    choice = message.text.strip()
    if choice not in QUESTION_FLOW["Q21_FamilyWork"]["options"]:
        await proceed_with_keyboard("Q21_FamilyWork", message, state)
        return

    await state.update_data(q21_family_work=choice)
    await proceed_with_keyboard("Q22_HousingType", message, state)


@router.message(StateFilter(QuestionnaireStates.Q22_HousingType))
async def questionnaire_housing_type(message: types.Message, state: FSMContext):
    choice = message.text.strip()
    if choice not in QUESTION_FLOW["Q22_HousingType"]["options"]:
        await proceed_with_keyboard("Q22_HousingType", message, state)
        return

    await state.update_data(q22_housing_type=choice)

    if choice == "☑️ Аренда":
        await message.answer(get_question_label("Q22_HousingDoc"), reply_markup=get_back_only_keyboard())
        await state.set_state(QuestionnaireStates.Q22_HousingDoc)
    else:
        await proceed_to_q23(message, state)



@router.message(F.content_type == types.ContentType.DOCUMENT, StateFilter(QuestionnaireStates.Q22_HousingDoc))
@router.message(F.content_type == types.ContentType.PHOTO, StateFilter(QuestionnaireStates.Q22_HousingDoc))
async def questionnaire_housing_doc(message: types.Message, state: FSMContext):
    if not is_allowed_file(message):
        await message.answer("❌ Прикрепите изображение или PDF договора аренды.")
        return

    file_id = message.document.file_id if message.document else message.photo[-1].file_id
    await state.update_data(q22_housing_doc=file_id)

    await message.answer("✅ Документ по жилью получен.")
    await proceed_to_q23(message, state)

async def proceed_to_q23(message: types.Message, state: FSMContext):
    await message.answer(get_question_label("Q24_AdditionalFile"), reply_markup=get_back_only_keyboard())
    await state.set_state(QuestionnaireStates.Q24_AdditionalFile)
    # await message.answer(get_question_label("Q23_Contribution"), reply_markup=get_back_only_keyboard())
    # await state.set_state(QuestionnaireStates.Q23_Contribution)


# @router.message(StateFilter(QuestionnaireStates.Q23_Contribution))
# async def questionnaire_contribution(message: types.Message, state: FSMContext):
#     raw = message.text.strip().replace(" ", "")
#     if not raw.isdigit():
#         await message.answer("❌ Введите только сумму в числовом формате, без текста.")
#         return

#     amount = int(raw)
#     await state.update_data(q23_contribution=amount)

#     flow = QUESTION_FLOW["Q23_Contribution"]
#     formatted = f"{amount:,}".replace(",", " ")

#     kb = ReplyKeyboardMarkup(
#         keyboard=[[KeyboardButton(text=btn)] for btn in flow["confirm_buttons"]],
#         resize_keyboard=True,
#         one_time_keyboard=True
#     )

#     text = flow["confirm_template"].format(amount=formatted)
#     await message.answer(text, reply_markup=kb, parse_mode="HTML")

#     await state.set_state(QuestionnaireStates.Q23_ContributionConfirm)


# @router.message(StateFilter(QuestionnaireStates.Q23_ContributionConfirm))
# async def questionnaire_contribution_confirm(message: types.Message, state: FSMContext):
#     flow = QUESTION_FLOW["Q23_Contribution"]
#     confirm, retry = flow["confirm_buttons"]

#     if message.text == confirm:
#         await message.answer(get_question_label("Q24_AdditionalFile"), reply_markup=get_back_only_keyboard())
#         await state.set_state(QuestionnaireStates.Q24_AdditionalFile)

#     elif message.text == retry:
#         await message.answer(get_question_label("Q23_Contribution"), reply_markup=ReplyKeyboardRemove())
#         await state.set_state(QuestionnaireStates.Q23_Contribution)

#     else:
#         await message.answer("❗ Пожалуйста, выберите один из предложенных вариантов.")



@router.message(
    F.content_type.in_({types.ContentType.DOCUMENT, types.ContentType.PHOTO}),
    StateFilter(QuestionnaireStates.Q24_AdditionalFile)
)
async def questionnaire_additional_file(message: types.Message, state: FSMContext):
    if not is_allowed_file(message):
        await message.answer("❌ Прикрепите изображение или PDF-документ.")
        return

    file_id = message.document.file_id if message.document else message.photo[-1].file_id
    await state.update_data(q24_additional_file=file_id)

    await proceed_with_keyboard("Q25_FinalComment", message, state)


@router.message(StateFilter(QuestionnaireStates.Q24_AdditionalFile))
async def skip_additional_file(message: types.Message, state: FSMContext):
    await state.update_data(q24_additional_file=None)
    await proceed_with_keyboard("Q25_FinalComment", message, state)


@router.message(StateFilter(QuestionnaireStates.Q25_FinalComment),  F.content_type == types.ContentType.TEXT)
async def questionnaire_final_comment(message: Message, state: FSMContext):
    await state.update_data(q25_final_comment=message.text)
    data = await state.get_data()

    full_name = data.get("q1_full_name")
    phone_number = data.get("q4_phone_number")
    birth_date_str = data.get("q2_birth_date")
    birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y").date()

    telegram_id = message.from_user.id
    bot_user = await sync_to_async(BotUser.objects.get)(telegram_id=telegram_id)

    existing_patient_qs = Patient.objects.filter(
        full_name=full_name,
        phone_number=phone_number,
        birth_date=birth_date
    )

    patient = await sync_to_async(existing_patient_qs.first)()
    folder_id = patient.folder_id if patient else None

    if not folder_id:
        folder_id = create_folder(f"Анкета пациента – {full_name}", parent_id=PARENT_FOLDER_ID)
        drive_folder_url = f"https://drive.google.com/drive/folders/{folder_id}"

        if not patient:
            patient = await sync_to_async(Patient.objects.create)(
                bot_user=bot_user,
                full_name=full_name,
                phone_number=phone_number,
                birth_date=birth_date,
                folder_id=folder_id,
                drive_folder_url=drive_folder_url
            )
        else:
            patient.folder_id = folder_id
            patient.drive_folder_url = drive_folder_url
            await sync_to_async(patient.save)()
    else:
        await message.answer("📁 Анкета уже была сохранена ранее для этого пациента. Старая папка будет использована повторно.")
    await message.answer("📂 Сохраняем данные анкеты...")

    try:
        await save_full_questionnaire_to_drive(data, message.bot, folder_id=folder_id)
        await message.answer("✅ Анкета успешно сохранена.")
    except Exception as e:
        await message.answer("⚠️ Ошибка при сохранении данных.")
        print(f"Error saving to Google Drive: {e}")

    summary = (
        "✅ <b>Анкета завершена!</b>\n\n"
        f"👤 <b>ФИО:</b> {data.get('q1_full_name')}\n"
        f"📅 <b>Дата рождения:</b> {data.get('q2_birth_date')}\n"
        f"🧑 <b>Пол:</b> {data.get('q3_gender')}\n"
        f"📞 <b>Телефон:</b> {data.get('q4_phone_number')}\n"
        f"📲 <b>Telegram:</b> {data.get('q5_telegram_username')}\n"
        f"👨‍👩‍👧‍👦 <b>Кто работает в семье:</b> {data.get('q21_family_work')}\n"
        f"🏠 <b>Тип жилья:</b> {data.get('q22_housing_type')}\n"
        f"📄 <b>Комментарий:</b> {data.get('q25_final_comment')}\n"
    )
    conclusion = calculate_final_conclusion(data)

    await message.answer(summary, parse_mode="HTML")
    await message.answer(format_conclusion_message(conclusion), parse_mode="HTML")

    await state.clear()
