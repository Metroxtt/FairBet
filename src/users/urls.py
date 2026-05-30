from django.urls import path
from . import views
from . import views_web

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='api-register'),
    path('me/', views.UserProfileView.as_view(), name='user-profile'),
    path('deposit-limits/', views.DepositLimitView.as_view(), name='deposit-limits'),
    path('self-exclude/', views.self_exclude, name='api-self-exclude'),
    path('verify-kyc/', views.verify_kyc, name='verify-kyc'),
]

urlpatterns_web = [
    path('', views_web.home_view, name='home'),
    path('login/', views_web.login_view, name='login'),
    path('logout/', views_web.logout_view, name='logout'),
    path('register/', views_web.register_view, name='register'),
    path('profile/', views_web.profile_view, name='profile'),
    path('kyc/', views_web.kyc_view, name='kyc'),
    path('deposit-limits/', views_web.deposit_limits_view, name='deposit-limits-web'),
    path('self-exclude/', views_web.self_exclude_view, name='self-exclude'),
    path('operator-dashboard/', views_web.operator_dashboard_view, name='operator-dashboard'),
    path('operator-dashboard/export-csv/', views_web.export_mincetur_csv, name='export-mincetur-csv'),
]
