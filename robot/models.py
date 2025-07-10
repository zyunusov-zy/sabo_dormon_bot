import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

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
    bot_user = models.ForeignKey('BotUser', on_delete=models.CASCADE, related_name="patients")
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    birth_date = models.DateField()
    folder_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
    folder_id = models.CharField(max_length=100, null=True, blank=True)
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
        self.update_status()
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

    def reject(self, by: str, comment: str = ""):
        """
        Отклоняет пациента с комментарием от врача или бухгалтера
        """
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


