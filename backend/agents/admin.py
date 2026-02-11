from django.contrib import admin
from .models import AgentMessage, AgentRunLog


@admin.register(AgentMessage)
class AgentMessageAdmin(admin.ModelAdmin):
    list_display = ('sender_agent', 'receiver_agent', 'intent', 'created_at')
    list_filter = ('sender_agent', 'receiver_agent', 'intent')
    search_fields = ('sender_agent', 'receiver_agent', 'intent')
    readonly_fields = ('created_at',)


@admin.register(AgentRunLog)
class AgentRunLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'run_type', 'status', 'started_at', 'completed_at')
    list_filter = ('run_type', 'status')
    readonly_fields = ('started_at',)
