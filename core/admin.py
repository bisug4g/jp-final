from django.contrib import admin
from .models import (
    UserProfile, DailyThought, DailyFlower, UserSession, DailyActivity
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_name', 'preferred_language', 'created_at']
    search_fields = ['user__username', 'display_name']


@admin.register(DailyThought)
class DailyThoughtAdmin(admin.ModelAdmin):
    list_display = ['content_preview', 'category', 'author', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['content', 'author']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content


@admin.register(DailyFlower)
class DailyFlowerAdmin(admin.ModelAdmin):
    list_display = ['name', 'season', 'is_active']
    list_filter = ['season', 'is_active']



@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'device_type', 'browser', 'os', 'is_active', 'created_at']
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['user__username', 'ip_address', 'browser']
    readonly_fields = ['created_at']


@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'login_count', 'notes_created', 'diary_entries', 'goals_created', 'tasks_completed']
    list_filter = ['date']
    search_fields = ['user__username']
