from django.contrib import admin
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


@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('ticket_id',)


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('message',)


@admin.register(SeafileLink)
class SeafileLinkAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'status', 'created_at')
    list_filter = ('status', 'created_at')


admin.site.register(IntegrationSettings)
admin.site.register(IntraServiceSettings)
admin.site.register(SeafileSettings)
admin.site.register(TelegramSettings)
admin.site.register(LogFilter)
admin.site.register(CategoryMapping)
admin.site.register(ProcessingHistory)
