from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication
from ..models import Patient
from ..serializers import PatientSerializer

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

        if role == "doctor":
            patient.approved_by_doctor = True
            patient.doctor_comment = comment
        elif role == "accountant":
            patient.approved_by_accountant = True
            patient.accountant_comment = comment
        else:
            return Response({"error": "⛔ У вас нет прав для одобрения"}, status=403)

        patient.save()
        patient.check_full_approval()
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

        if role == "doctor":
            patient.reject(by="doctor", comment=comment)
        elif role == "accountant":
            patient.reject(by="accountant", comment=comment)

        return Response(PatientSerializer(patient).data, status=status.HTTP_200_OK)