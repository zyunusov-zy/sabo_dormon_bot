import os
import io
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from aiogram import Bot
from googleapiclient.errors import HttpError
from robot.utils.misc.logging import log_handler, log_user_action, log_state_change, log_error, log_file_operation

load_dotenv(dotenv_path=".env", override=True)

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_PATH = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH')
PARENT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER_ID")


# print("[DEBUG] FOLDER_ID: ", PARENT_FOLDER_ID)
# print("[DEBUG] ACCOUNT: ", SERVICE_ACCOUNT_PATH)
QUESTION_LABELS = {
    "q1_full_name": "ФИО",
    "q2_birth_date": "Дата рождения",
    "q3_gender": "Пол",
    "q4_phone_number": "Телефон",
    "q5_telegram_username": "Telegram",
    "q6_region": "Регион",
    "q7_who_applies": "Кто обращается за помощью",
    "q8_is_sabodarmon": "Пациент Sabo?",
    "q9_source_info": "Как узнали о нас?",
    "q10_has_diagnosis": "Есть ли диагноз?",
    "q11_diagnosis_text": "Укажите диагноз",
    "q13_complaint": "Какие жалобы?",
    "q14_main_discomfort": "Что мешает больше всего?",
    "q15_improvements": "Что улучшится после лечения?",
    "q16_consequences": "Что будет, если не лечиться?",
    "q17_need_confirmation": "Нужны подтверждающие документы?",
    "q18_avg_income": "Средний доход на члена семьи (в млн сум)",
    "q19_children_count": "Сколько детей в семье?",
    "q21_family_work": "Кто работает в семье?",
    "q22_housing_type": "Какое у вас жильё?",
    # "q23_contribution": "Какую сумму вы готовы внести?",
    "q25_final_comment": "Комментарий к заявке",

    # Файлы
    "q12_diagnosis_file_id": "📎 Диагноз (файл)",
    "q17_confirmation_file": "📎 Подтверждающие документы (файл)",
    "q18_income_doc": "📎 Справка о доходах (файл)",
    "q19_children_docs": "📎 Документы на детей (файлы)",
    "q22_housing_doc": "📎 Документ на жильё (файл)",
    "q24_additional_file": "📎 Дополнительный файл",
}

QUESTION_FILE_KEYS = {
    "q12_diagnosis_file_id": "📎 Диагноз (файл)",
    "q17_confirmation_file": "📎 Подтверждающие документы (файл)",
    "q18_income_doc": "📎 Справка о доходах (файл)",
    "q19_children_docs": "📎 Документы на детей (файлы)",
    "q22_housing_doc": "📎 Документ на жильё (файл)",
    "q24_additional_file": "📎 Дополнительный файл",
}

def get_drive_service():
    if not SERVICE_ACCOUNT_PATH:
        raise ValueError("❌ GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH not set in .env file")
    
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        raise FileNotFoundError(f"❌ Service account file not found: {SERVICE_ACCOUNT_PATH}")
    
    creds = ServiceAccountCredentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def create_folder(name: str, parent_id: str = None) -> str:
    service = get_drive_service()
    metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id:
        metadata['parents'] = [parent_id]
    folder = service.files().create(body=metadata, fields='id').execute()
    return folder['id']

def upload_file_to_folder(file_bytes: bytes, filename: str, mime_type: str, folder_id: str) -> str:
    service = get_drive_service()
    metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type)
    uploaded_file = service.files().create(body=metadata, media_body=media, fields='id').execute()
    return uploaded_file['id']

def upload_text_to_drive(content: str, filename: str, folder_id: str = None) -> str:
    service = get_drive_service()
    metadata = {'name': filename, 'mimeType': 'text/plain'}
    if folder_id:
        metadata['parents'] = [folder_id]
    media = MediaIoBaseUpload(io.BytesIO(content.encode('utf-8')), mimetype='text/plain')
    file = service.files().create(body=metadata, media_body=media, fields='id').execute()
    return file['id']

async def save_file_by_id(file_id: str, folder_id: str, filename: str, bot: Bot, user_id: int = None):
    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_bytes = await bot.download_file(file_path)
        ext = os.path.splitext(file_path)[-1] or ".bin"

        mime_type = "application/octet-stream"
        if ext.lower() in ['.jpg', '.jpeg']:
            mime_type = "image/jpeg"
        elif ext.lower() == '.png':
            mime_type = "image/png"
        elif ext.lower() == '.pdf':
            mime_type = "application/pdf"
        elif ext.lower() in ['.doc', '.docx']:
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif ext.lower() == '.txt':
            mime_type = "text/plain"

        log_user_action(
            user_id=user_id,
            action="Uploading file",
            state="save_file_by_id",
            extra_data=f"Filename: {filename}{ext}, FolderID: {folder_id}"
        )

        return upload_file_to_folder(file_bytes.read(), f"{filename}{ext}", mime_type, folder_id)

    except Exception as e:
        log_error(
            user_id=user_id,
            error=e,
            action="Failed to upload file",
            state="save_file_by_id",
        )
        print(f"Error saving file {file_id}: {e}")
        raise


async def save_full_questionnaire_to_drive(user_data: dict, bot: Bot, folder_id: str, user_id: int = None):
    try:
        full_name = user_data.get('q1_full_name', 'Пациент')
        root_folder_id = folder_id

        text_parts = []

        if full_name:
            text_parts.append(f"ФИО: {full_name}")

        for key, value in user_data.items():
            if key == "q1_full_name" or key == "full_name":
                continue
            label = QUESTION_LABELS.get(key, key)

            if key in QUESTION_FILE_KEYS:
                if isinstance(value, list):
                    text_parts.append(f"{label}: {len(value)} файл(ов) ✅")
                else:
                    text_parts.append(f"{label}: Есть файл ✅" if value else f"{label}: —")
            else:
                text_parts.append(f"{label}: {value}")

        full_text = "\n".join(text_parts)

        log_user_action(
            user_id=user_id,
            action="Uploading questionnaire summary",
            state="save_full_questionnaire_to_drive",
            extra_data="Анкета.txt"
        )

        upload_text_to_drive(full_text, "Анкета.txt", folder_id=root_folder_id)

        # Загружаем вложения
        for field, folder_name in QUESTION_FILE_KEYS.items():
            file_value = user_data.get(field)
            if not file_value:
                continue

            subfolder_id = create_folder(folder_name, parent_id=root_folder_id)

            log_user_action(
                user_id=user_id,
                action="Created subfolder for attachments",
                state="save_full_questionnaire_to_drive",
                extra_data=f"{folder_name} (Field: {field})"
            )

            if isinstance(file_value, list):
                for idx, file_id in enumerate(file_value):
                    if file_id:
                        await save_file_by_id(file_id, subfolder_id, f"{folder_name}_{idx+1}", bot, user_id)
            else:
                await save_file_by_id(file_value, subfolder_id, folder_name, bot, user_id)

        log_user_action(
            user_id=user_id,
            action="Finished saving questionnaire",
            state="save_full_questionnaire_to_drive"
        )

    except Exception as e:
        log_error(
            user_id=user_id,
            error=e,
            action="Error saving questionnaire",
            state="save_full_questionnaire_to_drive",
        )
        print(f"❌ Error in save_full_questionnaire_to_drive: {e}")
        raise



def delete_folder(folder_id: str):
    try:
        service = get_drive_service()
        service.files().delete(fileId=folder_id).execute()
        print(f"✅ Папка с ID {folder_id} успешно удалена.")
        return True
    except HttpError as e:
        print(f"❌ Ошибка при удалении папки: {e}")
        return False
