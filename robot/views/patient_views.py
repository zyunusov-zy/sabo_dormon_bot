from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication
from ..models import Patient
from ..serializers import PatientSerializer
import logging

logger = logging.getLogger(__name__)

class PatientListView(generics.ListAPIView):
    queryset = Patient.objects.all().order_by('-created_at')
    serializer_class = PatientSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class ApprovePatientView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        token_payload = request.auth
        role = token_payload.get("role")

        patient = get_object_or_404(Patient, pk=pk)
        comment = request.data.get("comment", "")
        
        # Сохраняем предыдущий статус для логирования
        previous_status = patient.status

        if role == "doctor":
            patient.approved_by_doctor = True
            patient.rejected_by_doctor = False
            patient.doctor_comment = comment
            logger.info(f"Врач одобрил пациента {patient.patient_id}")
            
        elif role == "accountant":
            patient.approved_by_accountant = True
            patient.rejected_by_accountant = False
            patient.accountant_comment = comment
            logger.info(f"Бухгалтер одобрил пациента {patient.patient_id}")
        else:
            return Response({"error": "⛔ У вас нет прав для одобрения"}, status=403)

        # Сохраняем пациента (сигнал автоматически отправит уведомление)
        patient.save()
        patient.check_full_approval()
        
        logger.info(f"Статус пациента {patient.patient_id} изменен: {previous_status} -> {patient.status}")
        
        return Response(PatientSerializer(patient).data, status=200)


class RejectPatientView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        token_payload = request.auth
        role = token_payload.get("role")

        if role not in ["doctor", "accountant"]:
            return Response({"error": "⛔ У вас нет прав для отклонения"}, status=403)

        patient = get_object_or_404(Patient, pk=pk)
        comment = request.data.get("comment", "")
        
        # Сохраняем предыдущий статус для логирования
        previous_status = patient.status

        if role == "doctor":
            patient.reject(by="doctor", comment=comment)
            logger.info(f"Врач отклонил пациента {patient.patient_id}. Комментарий: {comment}")
        elif role == "accountant":
            patient.reject(by="accountant", comment=comment)
            logger.info(f"Бухгалтер отклонил пациента {patient.patient_id}. Комментарий: {comment}")

        logger.info(f"Статус пациента {patient.patient_id} изменен: {previous_status} -> {patient.status}")
        
        return Response(PatientSerializer(patient).data, status=status.HTTP_200_OK)


class SendNotificationView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk)
        
        from ..services.notification_service import notification_service
        
        try:
            result = notification_service.notify_patient_status_change(patient)
            
            if result:
                return Response({"success": "Уведомление отправлено"}, status=200)
            else:
                return Response({"error": "Не удалось отправить уведомление"}, status=500)
                
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {str(e)}")
            return Response({"error": str(e)}, status=500)