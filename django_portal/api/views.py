import os
from pathlib import Path
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
import markdown

from .models import (
    BotUser,
    Ticket,
    Log,
    SeafileLink,
    IntegrationSettings,
    IntraServiceSettings,
    SeafileSettings,
    TelegramSettings,
    LogFilter,
    CategoryMapping,
    ProcessingHistory,
)
from .serializers import (
    BotUserSerializer,
    TicketSerializer,
    LogSerializer,
    SeafileLinkSerializer,
    IntegrationSettingsSerializer,
    IntraServiceSettingsSerializer,
    SeafileSettingsSerializer,
    TelegramSettingsSerializer,
    LogFilterSerializer,
    CategoryMappingSerializer,
    ProcessingHistorySerializer,
)


class StaffPermission(permissions.IsAdminUser):
    """Restrict access to staff for configuration endpoints."""


class BotUserViewSet(viewsets.ModelViewSet):
    queryset = BotUser.objects.select_related('user').all()
    serializer_class = BotUserSerializer
    permission_classes = [StaffPermission]


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.select_related('ticket').all()
    serializer_class = LogSerializer


class SeafileLinkViewSet(viewsets.ModelViewSet):
    queryset = SeafileLink.objects.select_related('ticket').all()
    serializer_class = SeafileLinkSerializer


class IntegrationSettingsViewSet(viewsets.ModelViewSet):
    queryset = IntegrationSettings.objects.all()
    serializer_class = IntegrationSettingsSerializer
    permission_classes = [StaffPermission]


class IntraServiceSettingsViewSet(viewsets.ModelViewSet):
    queryset = IntraServiceSettings.objects.all()
    serializer_class = IntraServiceSettingsSerializer
    permission_classes = [StaffPermission]


class SeafileSettingsViewSet(viewsets.ModelViewSet):
    queryset = SeafileSettings.objects.all()
    serializer_class = SeafileSettingsSerializer
    permission_classes = [StaffPermission]


class TelegramSettingsViewSet(viewsets.ModelViewSet):
    queryset = TelegramSettings.objects.all()
    serializer_class = TelegramSettingsSerializer
    permission_classes = [StaffPermission]


class LogFilterViewSet(viewsets.ModelViewSet):
    queryset = LogFilter.objects.all()
    serializer_class = LogFilterSerializer
    permission_classes = [StaffPermission]


class CategoryMappingViewSet(viewsets.ModelViewSet):
    queryset = CategoryMapping.objects.all()
    serializer_class = CategoryMappingSerializer
    permission_classes = [StaffPermission]


class ProcessingHistoryViewSet(viewsets.ModelViewSet):
    queryset = ProcessingHistory.objects.select_related('ticket').all()
    serializer_class = ProcessingHistorySerializer


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health(request):
    return Response({'status': 'ok'})


class MetricsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        registry = CollectorRegistry()
        output = generate_latest(registry)
        return HttpResponse(output, content_type=CONTENT_TYPE_LATEST)


class TutorialView(View):
    template_name = 'tutorial.html'

    def get(self, request):
        base_dir = Path(__file__).resolve().parent.parent
        tutorial_path = base_dir / 'tutorial.md'
        markdown_text = tutorial_path.read_text(encoding='utf-8') if tutorial_path.exists() else "# Учебник\nОписание скоро появится."
        html = markdown.markdown(markdown_text)
        return render(request, self.template_name, {'content': html})


class SingleObjectEditor(View):
    model = None
    fields = []
    template_name = 'simple_form.html'
    success_redirect = '/'
    permission_class = StaffPermission

    def get_object(self):
        obj = self.model.objects.first()
        if not obj:
            obj = self.model()
        return obj

    def has_permission(self, request):
        return request.user.is_staff

    def get(self, request):
        if not self.has_permission(request):
            return redirect('/admin/login/?next=' + request.path)
        obj = self.get_object()
        fields_data = {field: getattr(obj, field) for field in self.fields}
        return render(request, self.template_name, {'object': obj, 'fields': self.fields, 'fields_data': fields_data})

    def post(self, request):
        if not self.has_permission(request):
            return redirect('/admin/login/?next=' + request.path)
        obj = self.get_object()
        for field in self.fields:
            value = request.POST.get(field, getattr(obj, field))
            setattr(obj, field, value)
        obj.save()
        return redirect(self.success_redirect)


class IntraServiceFormView(SingleObjectEditor):
    model = IntraServiceSettings
    fields = ['base_url', 'username', 'password', 'default_queue', 'is_active']
    success_redirect = '/intraservice-settings/'


class SeafileFormView(SingleObjectEditor):
    model = SeafileSettings
    fields = ['server_url', 'username', 'password', 'library_id', 'is_active']
    success_redirect = '/seafile-settings/'


class TelegramFormView(SingleObjectEditor):
    model = TelegramSettings
    fields = ['bot_token', 'chat_id', 'webhook_url', 'is_active']
    success_redirect = '/telegram-settings/'


class LogFilterEditorView(SingleObjectEditor):
    model = LogFilter
    fields = ['name', 'pattern', 'is_active']
    success_redirect = '/log-filters/'


class LinkStatusTableView(View):
    template_name = 'links.html'

    def get(self, request):
        links = SeafileLink.objects.select_related('ticket').all()
        return render(request, self.template_name, {'links': links})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def workflow_results(request):
    ProcessingHistory.objects.create(
        ticket=None,
        status=request.data.get('status', 'ok'),
        details=request.data.get('details', ''),
        processed_by=request.user,
    )
    return Response({'status': 'ok'})
