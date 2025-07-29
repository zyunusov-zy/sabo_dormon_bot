from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Message


QUESTION_COUNT = 25

QUESTION_FLOW = {
    "Q1_FullName": {
        "label": "Введите Ф.И.О. пациента полностью (пример: Ivanov Ivan Ivanovich):",
        "input_type": "text"
    },
    "Q2_BirthDate": {
        "label": "Выберите дату рождения пациента 📅",
        "input_type": "date",
        "back_button": True
    },
    "Q3_Gender": {
        "label": "Укажите пол пациента:",
        "options": ["Мужской", "Женский"],
        "input_type": "buttons",
        "back_button": True
    },
    "Q4_PhoneNumber": {
        "label": "Пожалуйста, отправьте номер телефона пациента через кнопку ниже:",
        "input_type": "contact",
        "back_button": True
    },
    "Q5_TelegramUsername": {
        "label": "Пожалуйста, отправьте ваш Telegram username через кнопку ниже:",
        "input_type": "username",
        "back_button": True
    },
    "Q6_Region": {
        "label": "📍 Пожалуйста, выберите регион и город проживания из списка ниже или нажмите «Другое» для ручного ввода.",
        "options": [],
        "input_type": "text",
        "back_button": True
    },
    "Q7_WhoApplies": {
        "label": "Кто обращается?",
        "options": ["Сам(а)", "Родственник"],
        "input_type": "buttons",
        "back_button": True
    },
    "Q8_SaboPatient": {
        "label": "Является ли пациентом Сабо-Дармон?",
        "options": ["Да", "Нет", "Неизвестно"],
        "input_type": "buttons",
        "back_button": True
    },
    "Q9_HowFound": {
        "label": "Откуда вы узнали о программе?",
        "options": ["Telegram", "Instagram", "Клиника", "Знакомые", "Другое"],
        "input_type": "buttons",
        "back_button": True
    },
    "Q10_HasDiagnosis": {
        "label": "Есть ли установленный диагноз?",
        "options": ["✅ Да", "❌ Нет"],
        "input_type": "buttons",
        "back_button": True
    },
    "Q11_DiagnosisText": {
        "label": "Укажите диагноз пациента:",
        "input_type": "text",
        "back_button": True
    },
    "Q12_DiagnosisFile": {
        "label": "Прикрепите фото/скан диагноза или эпикриза.",
        "input_type": "file_optional",
        "back_button": True
    },
    "Q13_Complaint": {
        "label": "Введите кратко жалобу / причину обращения:",
        "input_type": "text",
        "back_button": True
    },
    "Q14_MainDiscomfort": {
        "label": "Что доставляет вам наибольшие неудобства от текущей болезни?",
        "options": ["Боль", "Нарушение сна", "Невозможность работать", "Ограничение в передвижении", "Другое"],
        "input_type": "buttons_optional_text",
        "back_button": True
    },
    "Q15_ImprovementsAfterTreatment": {
        "label": "Что изменится после лечения?\n\nВыберите всё, что подходит, по одному пункту. Когда закончите — нажмите ✅ Готово.",
        "options": [
            "☑️ Смогу работать / учиться", "☑️ Самообслуживание",
            "☑️ Уменьшится боль", "☑️ Снижение риска осложнений",
            "☑️ Улучшится сон / энергия", "☑️ Другое"
        ],
        "finish_button": "✅ Готово",
        "input_type": "multi_buttons",
        "back_button": True
    },
    "Q16_WithoutTreatmentConsequences": {
        "label": "Что будет, если не лечиться?\n\nВыберите всё, что подходит, по одному пункту. Когда закончите — нажмите ✅ Завершить выбор.",
        "options": [
            "☑️ Ухудшение состояния", "☑️ Потеря трудоспособности",
            "☑️ Риск инвалидности", "☑️ Неизвестно"
        ],
        "finish_button": "✅ Завершить выбор",
        "input_type": "multi_buttons",
        "back_button": True
    },
    "Q17_NeedConfirmationDocs": {
        "label": "📄 Есть ли подтверждение нуждаемости от махалли или других органов?",
        "options": ["☑️ Да, есть", "☑️ Нет, но можем взять", "☑️ Нет"],
        "input_type": "buttons",
        "back_button": True
    },
    "Q17_ConfirmationFile": {
        "label": "📎 Прикрепите документ: справку о нуждаемости, 'темир дафтар' и т.п. (фото или PDF).",
        "input_type": "file",
        "back_button": True
    },
    "Q18_AvgIncome": {
        "label": "📊 Укажите средний доход вашей семьи в месяц:",
        "options": ["До 5 млн", "5–7 млн", "7–10 млн", "10+ млн"],
        "input_type": "buttons",
        "back_button": True
    },
    "Q18_IncomeDoc": {
        "label": "📎 Прикрепите подтверждающий документ (справка о доходах, выписка и т.п.).",
        "input_type": "file",
        "back_button": True
    },
    "Q19_ChildrenCount": {
        "label": "👶 Сколько несовершеннолетних детей в семье?",
        "options": ["0", "1", "2", "3", "4", "5+"],
        "input_type": "buttons",
        "back_button": True
    },
    "Q19_ChildrenDocs": {
        "label": "📎 Прикрепите метрику каждого ребёнка (фото или PDF). После загрузки всех файлов нажмите «✅ Завершить загрузку».",
        "input_type": "file_multiple",
        "back_button": True
    },
    "Q21_FamilyWork": {
        "label": "👨‍💼 Кто работает в семье?",
        "options": ["☑️ Только муж", "☑️ Оба", "☑️ Никто", "☑️ Только жена", "☑️ Пенсионер"],
        "input_type": "buttons",
        "back_button": True
    },
    "Q22_HousingType": {
        "label": "🏠 Какой у вас тип жилья?",
        "options": ["☑️ Собственное", "☑️ Аренда", "☑️ У родственников"],
        "input_type": "buttons",
        "back_button": True
    },
    "Q22_HousingDoc": {
        "label": "📎 Прикрепите договор аренды или иной подтверждающий документ, зарегистрированный в налоговой (например, свидетельство, уведомление или справка).",
        "input_type": "file",
        "back_button": True
    },
    # "Q23_Contribution": {
    #     "label": "💰 До какой суммы вы можете оплатить лечение? (в сумах)",
    #     "input_type": "currency_confirm",
    #     "confirm_buttons": ["✅ Да, всё верно", "🔁 Ввести снова"],
    #     "confirm_template": "💵 Вы указали: <b>{amount} сум</b>.\nПодтвердите, пожалуйста:",
    #     "back_button": True
    # },
    "Q24_AdditionalFile": {
        "label": "📎 Прикрепите дополнительный файл, подтверждающий ваши обстоятельства (необязательно).\nЕсли хотите пропустить — отправьте точку (.) или любой символ.",
        "input_type": "file_optional",
        "back_button": True
    },
    "Q25_FinalComment": {
        "label": "📝 Есть ли у вас другие важные обстоятельства, которые помогут Клинике Сабо Дормон принять правильное решение по вашему делу?",
        "input_type": "text",
        "back_button": True
    }
}


def get_question_label(state_name: str) -> str:
    question_keys = list(QUESTION_FLOW.keys())
    index = question_keys.index(state_name) + 1
    total = len(question_keys)
    label = QUESTION_FLOW[state_name]["label"]
    return f"🔹 Вопрос {index} из {total}:\n{label}"

def get_keyboard_for(state_name: str) -> ReplyKeyboardMarkup | None:
    options = QUESTION_FLOW[state_name].get("options")
    if not options:
        return None

    rows = [options[i:i+2] for i in range(0, len(options), 2)]

    if QUESTION_FLOW[state_name].get("back_button"):
        rows.append(["⬅️ Назад"])

    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=opt) for opt in row] for row in rows],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_multi_choice_keyboard(state_name: str) -> ReplyKeyboardMarkup:
    options = QUESTION_FLOW[state_name]["options"]
    finish = QUESTION_FLOW[state_name]["finish_button"]

    rows = [options[i:i+2] for i in range(0, len(options), 2)]
    rows.append([finish])

    if QUESTION_FLOW[state_name].get("back_button"):
        rows.append(["⬅️ Назад"])

    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=opt) for opt in row] for row in rows],
        resize_keyboard=True
    )
