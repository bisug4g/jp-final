from django.contrib import admin

from .models import TangredProject, TangredScreen, TangredSession, TangredSessionPhoto


@admin.register(TangredProject)
class TangredProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "stitch_project_id", "created_at", "last_synced_at")
    search_fields = ("title", "stitch_project_id", "user__username")


@admin.register(TangredScreen)
class TangredScreenAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "device_type", "model_id", "created_at")
    search_fields = ("title", "stitch_screen_id", "stitch_screen_name", "project__title")


@admin.register(TangredSession)
class TangredSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "status", "style_identity", "created_at")
    search_fields = ("title", "user__username", "style_identity")


@admin.register(TangredSessionPhoto)
class TangredSessionPhotoAdmin(admin.ModelAdmin):
    list_display = ("session", "caption", "created_at")
    search_fields = ("session__title", "caption")
