from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Patient
from .services.notification_service import notification_service
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Patient)
def store_previous_status(sender, instance, **kwargs):
    """Сохраняем предыдущий статус перед сохранением"""
    if instance.pk:
        try:
            previous = Patient.objects.get(pk=instance.pk)
            instance._previous_status = previous.status
        except Patient.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None

@receiver(post_save, sender=Patient)
def notify_patient_status_change(sender, instance, created, **kwargs):
    """Отправляем уведомление при изменении статуса"""
    
    if created:
        return
    
    previous_status = getattr(instance, '_previous_status', None)
    current_status = instance.status
    
    if previous_status != current_status and current_status != "waiting":
        logger.info(f"Отправка уведомления пациенту {instance.patient_id}: {previous_status} -> {current_status}")
        
        try:
            notification_service.notify_patient_status_change(
                patient=instance,
                previous_status=previous_status
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пациенту {instance.patient_id}: {str(e)}")

@receiver(post_save, sender=Patient)
def log_patient_status_change(sender, instance, created, **kwargs):
    """Логируем изменения статуса пациента"""
    if not created:
        previous_status = getattr(instance, '_previous_status', None)
        if previous_status != instance.status:
            logger.info(f"Пациент {instance.patient_id} ({instance.full_name}): статус изменился с '{previous_status}' на '{instance.status}'")