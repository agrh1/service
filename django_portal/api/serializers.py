from rest_framework import serializers
from .models import Ticket, Log, SeafileLink

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'ticket_id', 'status', 'created_at', 'updated_at']

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ['id', 'ticket', 'message', 'created_at']

class SeafileLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeafileLink
        fields = ['id', 'ticket', 'upload_link', 'download_link', 'password', 'created_at']

