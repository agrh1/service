from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'bot-users', views.BotUserViewSet)
router.register(r'tickets', views.TicketViewSet)
router.register(r'logs', views.LogViewSet)
router.register(r'links', views.SeafileLinkViewSet)
router.register(r'integrations', views.IntegrationSettingsViewSet)
router.register(r'intraservice', views.IntraServiceSettingsViewSet)
router.register(r'seafile', views.SeafileSettingsViewSet)
router.register(r'telegram', views.TelegramSettingsViewSet)
router.register(r'log-filters', views.LogFilterViewSet)
router.register(r'category-mapping', views.CategoryMappingViewSet)
router.register(r'processing-history', views.ProcessingHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('workflow-results/', views.workflow_results),
]
