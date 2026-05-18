from django.contrib import admin
from .models import Tag, NoteFolder, Note


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color']
    search_fields = ['name']


@admin.register(NoteFolder)
class NoteFolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'user__username']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'folder', 'is_pinned', 'created_at', 'modified_at']
    list_filter = ['is_pinned', 'created_at']
    search_fields = ['title', 'content_plain', 'user__username']
    readonly_fields = ['created_at', 'modified_at']
