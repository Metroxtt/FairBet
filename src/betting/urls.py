from django.urls import path
from . import views

urlpatterns = [
    path('', views.BetHistoryView.as_view(), name='bet-history'),
    path('place/', views.place_bet, name='place-bet'),
    path('<int:bet_id>/cashout/', views.cashout_bet, name='cashout-bet'),
]
