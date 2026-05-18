from django.contrib import admin
from .models import Goal, Task, Milestone


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'completion_percentage', 'target_date', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'goal', 'status', 'due_date', 'completion_percentage']
    list_filter = ['status', 'due_date']
    search_fields = ['title', 'goal__title']


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['title', 'goal', 'target_date', 'is_achieved']
    list_filter = ['is_achieved', 'target_date']
    search_fields = ['title', 'goal__title']
