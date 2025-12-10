from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api import views as api_views


def metrics(_request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('health/', health),
    path('metrics/', metrics),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('health/', api_views.health, name='health'),
    path('metrics/', api_views.MetricsView.as_view(), name='metrics'),
    path('tutorial/', api_views.TutorialView.as_view(), name='tutorial'),
    path('intraservice-settings/', api_views.IntraServiceFormView.as_view(), name='intraservice_settings'),
    path('seafile-settings/', api_views.SeafileFormView.as_view(), name='seafile_settings'),
    path('telegram-settings/', api_views.TelegramFormView.as_view(), name='telegram_settings'),
    path('log-filters/', api_views.LogFilterEditorView.as_view(), name='log_filters'),
    path('links/', api_views.LinkStatusTableView.as_view(), name='link_status'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
