from rest_framework import serializers
from .models import Patient
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from rest_framework import serializers
from .models import Patient

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = [
            'patient_id',
            'status',
            'is_fully_approved',
            'is_rejected',
            'rejected_by_doctor',
            'rejected_by_accountant',
            'approved_by_doctor',
            'approved_by_accountant',
            'created_at',
        ]



from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['role'] = user.role

        return token
