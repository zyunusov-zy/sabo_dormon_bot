import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class BotUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('doctor', 'Врач'),
        ('accountant', 'Бухгалтер'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    def __str__(self):
        return f"{self.username} ({self.role})"

class Patient(models.Model):
    patient_id = models.CharField(max_length=20, unique=True, editable=False)
    bot_user = models.OneToOneField('BotUser', on_delete=models.CASCADE, related_name="patient")  # Изменено на OneToOneField
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    birth_date = models.DateField()
    folder_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Добавить поле для отслеживания даты одобрения
    approved_at = models.DateTimeField(null=True, blank=True)

    # Одобрения и отказы
    approved_by_doctor = models.BooleanField(default=False)
    approved_by_accountant = models.BooleanField(default=False)
    is_fully_approved = models.BooleanField(default=False)

    rejected_by_doctor = models.BooleanField(default=False)
    rejected_by_accountant = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)

    # Комментарии
    doctor_comment = models.TextField(blank=True, null=True)
    accountant_comment = models.TextField(blank=True, null=True)

    # Google Drive
    drive_folder_url = models.URLField(blank=True, null=True)

    # Статус
    STATUS_CHOICES = [
        ("waiting", "⏳ В ожидании"),
        ("approved_by_doctor", "✅ Одобрено врачом"),
        ("approved_by_accountant", "✅ Одобрено бухгалтером"),
        ("fully_approved", "🟢 Полностью одобрено"),
        ("rejected", "❌ Отклонено"),
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="waiting")

    def save(self, *args, **kwargs):
        if not self.patient_id:
            self.patient_id = f"PAT-{uuid.uuid4().hex[:6].upper()}"
        
        # Обновляем дату одобрения при полном одобрении
        old_fully_approved = False
        if self.pk:
            old_instance = Patient.objects.get(pk=self.pk)
            old_fully_approved = old_instance.is_fully_approved
        
        self.update_status()
        
        # Устанавливаем дату одобрения при первом полном одобрении
        if self.is_fully_approved and not old_fully_approved:
            self.approved_at = timezone.now()
        
        super().save(*args, **kwargs)

    def update_status(self):
        if self.rejected_by_doctor or self.rejected_by_accountant:
            self.status = "rejected"
            self.is_rejected = True
            self.is_fully_approved = False
        elif self.approved_by_doctor and self.approved_by_accountant:
            self.status = "fully_approved"
            self.is_fully_approved = True
            self.is_rejected = False
        elif self.approved_by_doctor:
            self.status = "approved_by_doctor"
            self.is_rejected = False
        elif self.approved_by_accountant:
            self.status = "approved_by_accountant"
            self.is_rejected = False
        else:
            self.status = "waiting"
            self.is_rejected = False
            self.is_fully_approved = False

    def can_register_again(self):
        """Проверяет, может ли пользователь подать новую анкету"""
        if self.is_fully_approved and self.approved_at:
            # Если одобрен, проверяем прошло ли 7 месяцев
            seven_months_ago = timezone.now() - timedelta(days=7*30)  # Примерно 7 месяцев
            return self.approved_at <= seven_months_ago
        elif self.is_rejected:
            # Если отклонен, может подать снова
            return True
        else:
            # Если анкета на рассмотрении, не может подать новую
            return False

    def reject(self, by: str, comment: str = ""):
        """Отклоняет пациента с комментарием от врача или бухгалтера"""
        if by == "doctor":
            self.rejected_by_doctor = True
            self.approved_by_doctor = False
            self.doctor_comment = comment
        elif by == "accountant":
            self.rejected_by_accountant = True
            self.approved_by_accountant = False
            self.accountant_comment = comment

        self.is_rejected = True
        self.approved_by_doctor = False
        self.approved_by_accountant = False
        self.is_fully_approved = False
        self.approved_at = None  # Сбрасываем дату одобрения

        self.save()

    def check_full_approval(self):
        self.is_fully_approved = (
            self.approved_by_doctor and self.approved_by_accountant
            and not self.rejected_by_doctor and not self.rejected_by_accountant
        )
        self.update_status()
        self.save()

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"