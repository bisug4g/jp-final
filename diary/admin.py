from django.contrib import admin
from .models import DiaryEntry, DiaryPrompt, MoodSummary


@admin.register(DiaryEntry)
class DiaryEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'entry_date', 'mood', 'input_method', 'created_at']
    list_filter = ['mood', 'input_method', 'entry_date']
    search_fields = ['user__username', 'content']
    readonly_fields = ['created_at']
    date_hierarchy = 'entry_date'


@admin.register(DiaryPrompt)
class DiaryPromptAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['question']


@admin.register(MoodSummary)
class MoodSummaryAdmin(admin.ModelAdmin):
    list_display = ['user', 'week_start', 'avg_mood', 'entry_count']
    list_filter = ['week_start']
    search_fields = ['user__username']
