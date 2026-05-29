from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('me/', views.UserProfileView.as_view(), name='user-profile'),
    path('deposit-limits/', views.DepositLimitView.as_view(), name='deposit-limits'),
    path('self-exclude/', views.self_exclude, name='self-exclude'),
    path('verify-kyc/', views.verify_kyc, name='verify-kyc'),
]
