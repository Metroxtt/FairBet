from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.EventViewSet, basename='event')
router.register(r'markets', views.MarketViewSet, basename='market')

urlpatterns = [
    path('', include(router.urls)),
]
