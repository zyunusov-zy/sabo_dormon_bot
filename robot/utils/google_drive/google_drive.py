import os
import io
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from aiogram import Bot

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_PATH = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH')
PARENT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER_ID")


QUESTION_FILE_KEYS = {
    "q12_diagnosis_file_id": "Q12_DiagnosisFile",
    "q17_confirmation_file": "Q17_ConfirmationFile",
    "q18_income_doc": "Q18_IncomeDoc",
    "q19_children_docs": "Q19_ChildrenDocs",
    "q20_housing_doc": "Q20_HousingDoc",
    "q22_additional_file": "Q22_AdditionalFile"
}

def get_drive_service():
    print(f"SERVICE_ACCOUNT_PATH: {SERVICE_ACCOUNT_PATH}")
    print(f"SERVICE_ACCOUNT_PATH exists: {os.path.exists(SERVICE_ACCOUNT_PATH) if SERVICE_ACCOUNT_PATH else False}")
    
    if not SERVICE_ACCOUNT_PATH:
        raise ValueError("❌ GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH not set in .env file")
    
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        raise FileNotFoundError(f"❌ Service account file not found: {SERVICE_ACCOUNT_PATH}")
    
    print("Using Service Account authentication")
    try:
        creds = ServiceAccountCredentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        print("✅ Google Drive service authenticated successfully")
        return service
    except Exception as e:
        print(f"❌ Error creating Google Drive service: {e}")
        raise

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

async def save_file_by_id(file_id: str, folder_id: str, filename: str, bot: Bot):
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
        
        return upload_file_to_folder(file_bytes.read(), f"{filename}{ext}", mime_type, folder_id)
    except Exception as e:
        print(f"Error saving file {file_id}: {e}")
        raise

async def save_full_questionnaire_to_drive(user_data: dict, bot: Bot):
    try:
        full_name = user_data.get('q1_full_name', 'Пациент')
        root_folder_name = f"Анкета пациента – {full_name}"
        
        print(f"Creating root folder: {root_folder_name}")
        root_folder_id = create_folder(root_folder_name, parent_id=PARENT_FOLDER_ID)
        print(f"Root folder created with ID: {root_folder_id}")

        text_parts = []
        for key, value in user_data.items():
            if key not in QUESTION_FILE_KEYS and not isinstance(value, list):
                text_parts.append(f"{key}: {value}")
        full_text = "\n".join(text_parts)

        print("Uploading questionnaire text file...")
        text_file_id = upload_text_to_drive(full_text, "Анкета.txt", folder_id=root_folder_id)
        print(f"Text file uploaded with ID: {text_file_id}")

        for field, folder_name in QUESTION_FILE_KEYS.items():
            file_value = user_data.get(field)
            if not file_value:
                continue

            print(f"Processing files for {field}: {file_value}")
            subfolder_id = create_folder(folder_name, parent_id=root_folder_id)
            print(f"Created subfolder {folder_name} with ID: {subfolder_id}")

            if isinstance(file_value, list):
                for idx, file_id in enumerate(file_value):
                    if file_id:
                        await save_file_by_id(file_id, subfolder_id, f"{folder_name}_{idx+1}", bot)
                        print(f"Uploaded file {idx+1} for {field}")
            else:
                if file_value:
                    await save_file_by_id(file_value, subfolder_id, folder_name, bot)
                    print(f"Uploaded single file for {field}")
        
        print("All files uploaded successfully!")
        
    except Exception as e:
        print(f"Error in save_full_questionnaire_to_drive: {e}")
        raise