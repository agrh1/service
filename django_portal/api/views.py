from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Ticket, Log, SeafileLink
from .serializers import TicketSerializer, LogSerializer, SeafileLinkSerializer

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer

class SeafileLinkViewSet(viewsets.ModelViewSet):
    queryset = SeafileLink.objects.all()
    serializer_class = SeafileLinkSerializer

@api_view(['GET'])
def health(request):
    return Response({'status': 'ok'})

@api_view(['POST'])
def workflow_results(request):
    """Сохранить результаты workflow"""
    return Response({'status': 'ok'})

