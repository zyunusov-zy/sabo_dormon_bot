import logging
import requests
from django.conf import settings
from ..models import Patient

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.bot_token = settings.BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML"):
        """Отправка сообщения в Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Сообщение успешно отправлено пациенту {chat_id}")
                return True
            else:
                logger.error(f"Ошибка отправки сообщения: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {str(e)}")
            return False
    
    def notify_patient_status_change(self, patient: Patient, previous_status: str = None):
        """Уведомление пациента об изменении статуса"""
        
        if not patient.bot_user or not patient.bot_user.telegram_id:
            logger.warning(f"У пациента {patient.patient_id} нет telegram_id")
            return False
        
        message = self._build_status_message(patient, previous_status)
        
        return self.send_message(
            chat_id=patient.bot_user.telegram_id,
            text=message
        )
    
    def _build_status_message(self, patient: Patient, previous_status: str = None):
        """Формирование сообщения в зависимости от статуса"""
        
        messages = {
            "approved_by_doctor": {
                "title": "✅ Одобрено врачом",
                "text": f"Ваша анкета одобрена врачом!\n\n"
                       f"📋 ID пациента: <code>{patient.patient_id}</code>\n"
                       f"👤 ФИО: {patient.full_name}\n"
                       f"📞 Телефон: {patient.phone_number}\n\n"
                       f"⏳ Ожидаем одобрения от бухгалтера..."
            },
            
            "approved_by_accountant": {
                "title": "✅ Одобрено бухгалтером", 
                "text": f"Ваша анкета одобрена бухгалтером!\n\n"
                       f"📋 ID пациента: <code>{patient.patient_id}</code>\n"
                       f"👤 ФИО: {patient.full_name}\n"
                       f"📞 Телефон: {patient.phone_number}\n\n"
                       f"⏳ Ожидаем одобрения от врача..."
            },
            
            "fully_approved": {
                "title": "🟢 Полностью одобрено",
                "text": f"🎉 Поздравляем! Ваша анкета полностью одобрена!\n\n"
                       f"📋 ID пациента: <code>{patient.patient_id}</code>\n"
                       f"👤 ФИО: {patient.full_name}\n"
                       f"📞 Телефон: {patient.phone_number}\n\n"
                       f"✅ Одобрено врачом\n"
                       f"✅ Одобрено бухгалтером\n\n"
                       f"📝 Вы можете обратиться в клинику для получения услуг."
            },
            
            "rejected": {
                "title": "❌ Отклонено",
                "text": f"😔 К сожалению, ваша анкета была отклонена.\n\n"
                       f"📋 ID пациента: <code>{patient.patient_id}</code>\n"
                       f"👤 ФИО: {patient.full_name}\n"
                       f"📞 Телефон: {patient.phone_number}\n\n"
                    #    f"📝 <b>Причины отклонения:</b>\n"
            }
        }
        
        # if patient.status == "rejected":
        #     reasons = []
        #     if patient.rejected_by_doctor and patient.doctor_comment:
        #         reasons.append(f"👨‍⚕️ Врач: {patient.doctor_comment}")
        #     if patient.rejected_by_accountant and patient.accountant_comment:
        #         reasons.append(f"👩‍💼 Бухгалтер: {patient.accountant_comment}")
            
        #     if reasons:
        #         messages["rejected"]["text"] += "\n".join(reasons)
        #     else:
        #         messages["rejected"]["text"] += "Причина не указана."
            
        #     messages["rejected"]["text"] += "\n\n🔄 Вы можете подать анкету заново, устранив указанные недостатки."
        
        # Добавляем комментарии для одобренных статусов
        if patient.status in ["approved_by_doctor", "approved_by_accountant", "fully_approved"]:
            comments = []
            if patient.approved_by_doctor and patient.doctor_comment:
                comments.append(f"👨‍⚕️ Комментарий врача: {patient.doctor_comment}")
            if patient.approved_by_accountant and patient.accountant_comment:
                comments.append(f"👩‍💼 Комментарий бухгалтера: {patient.accountant_comment}")
            
            if comments:
                messages[patient.status]["text"] += "\n\n📝 <b>Комментарии:</b>\n" + "\n".join(comments)
        
        return messages.get(patient.status, {}).get("text", "Статус вашей анкеты изменился.")


# Создаем экземпляр сервиса
notification_service = NotificationService()