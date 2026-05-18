from django.contrib import admin
from .models import AIConversation, AIMessage


class AIMessageInline(admin.TabularInline):
    model = AIMessage
    extra = 0
    readonly_fields = ['timestamp']


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at', 'message_count']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AIMessageInline]

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
