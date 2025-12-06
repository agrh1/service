from django.contrib import admin
from .models import Ticket, Log, SeafileLink

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['ticket_id']

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'created_at']
    list_filter = ['created_at']
    search_fields = ['message']

@admin.register(SeafileLink)
class SeafileLinkAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'created_at']
    list_filter = ['created_at']

