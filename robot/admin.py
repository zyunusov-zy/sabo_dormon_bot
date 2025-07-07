from django.contrib import admin
from .models import BotUser, Patient 

@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = ("id", "telegram_id", "full_name", "phone_number", "created_at")
    search_fields = ("full_name", "telegram_id", "phone_number")

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "full_name", "phone_number", "birth_date", "bot_user", "created_at")
    search_fields = ("full_name", "phone_number", "bot_user__telegram_id", "patient_id")
    list_filter = ("created_at",)