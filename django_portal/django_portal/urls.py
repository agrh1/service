from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

def health(request):
    return JsonResponse({'status': 'ok'})


def metrics(_request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('health/', health),
    path('metrics/', metrics),
]
