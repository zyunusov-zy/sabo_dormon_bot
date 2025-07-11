from django.urls import path
from .views.patient_views import PatientListView, ApprovePatientView, RejectPatientView, SendNotificationView
from .views.auth_views import CustomLoginView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('token/', CustomLoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('patients/', PatientListView.as_view(), name='patient-list'),
    path('patients/<int:pk>/approve/', ApprovePatientView.as_view(), name='patient-approve'),
    path("patients/<int:pk>/reject/", RejectPatientView.as_view(), name="reject-patient"),
    path('patients/<int:pk>/notify/', SendNotificationView.as_view(), name='send-notification'),
]
