from django.urls import path
from . import views

urlpatterns = [
    path('balance/', views.BalanceView.as_view(), name='wallet-balance'),
    path('transactions/', views.TransactionHistoryView.as_view(), name='wallet-transactions'),
    path('deposit/', views.deposit, name='wallet-deposit'),
    path('withdraw/', views.withdraw, name="wallet-withdraw"),
]
