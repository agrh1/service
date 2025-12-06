from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tickets', views.TicketViewSet)
router.register(r'logs', views.LogViewSet)
router.register(r'links', views.SeafileLinkViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.health),
    path('workflow-results/', views.workflow_results),
]

