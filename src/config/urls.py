from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as static_serve
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.urls import urlpatterns_web
from events.views import event_list_view
from wallet.views import wallet_index_view
from betting.views import betting_history_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/wallet/', include('wallet.urls')),
    path('api/events/', include('events.urls')),
    path('api/bets/', include('betting.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Rutas web (templates)
    path('', include(urlpatterns_web)),
    path('events/', event_list_view, name='events'),
    path('wallet/', wallet_index_view, name='wallet'),
    path('bets/', betting_history_view, name='bets'),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', static_serve, {'document_root': settings.STATIC_ROOT}),
    ]
