from django.urls import path
from . import views

urlpatterns = [
    path('', views.BetHistoryView.as_view(), name='bet-history'),
    path('place/', views.place_bet, name='place-bet'),
    path('combo/place/', views.place_combo_bet, name='place-combo-bet'),
    path('<int:bet_id>/cashout/', views.cashout_bet, name='cashout-bet'),
    path('admin/settle-event/', views.admin_settle_event, name='admin-settle-event'),
    path('admin/suspend-market/', views.admin_suspend_market, name='admin-suspend-market'),
]
