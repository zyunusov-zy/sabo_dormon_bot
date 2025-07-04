from django.contrib import admin
from .models import BotUser

@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone_number", "telegram_id", "created_at")
    search_fields = ("full_name", "phone_number", "telegram_id")
