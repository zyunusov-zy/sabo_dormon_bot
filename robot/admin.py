from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import BotUser, Patient, CustomUser

@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = ("id", "telegram_id", "full_name", "phone_number", "created_at")
    search_fields = ("full_name", "telegram_id", "phone_number")

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'phone_number',
        'folder_id',
        'approved_by_doctor',
        'approved_by_accountant',
        'rejected_by_doctor',
        'rejected_by_accountant',
        'is_rejected',
        'is_fully_approved',
        'status',
    )
    list_filter = (
        'approved_by_doctor',
        'approved_by_accountant',
        'rejected_by_doctor',
        'rejected_by_accountant',
        'is_rejected',
        'is_fully_approved',
        'status',
    )
    search_fields = ('full_name', 'phone_number')
    readonly_fields = ('is_fully_approved', 'is_rejected', 'status', 'patient_id')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)              
        obj.check_full_approval()


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ("Роль пользователя", {"fields": ("role",)}),
    )