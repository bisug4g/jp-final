import uuid

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class TangredProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tangred_projects")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    stitch_project_id = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-modified_at"]

    def __str__(self):
        return self.title

    @property
    def latest_screen(self):
        return self.screens.order_by("-created_at").first()


class TangredSession(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("PROCESSING", "Processing"),
        ("READY", "Ready"),
        ("ERROR", "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tangred_sessions")
    title = models.CharField(max_length=255)
    occasion = models.CharField(max_length=120, blank=True)
    body_frame = models.CharField(max_length=120, blank=True)
    skin_tone = models.CharField(max_length=120, blank=True)
    preferred_palette = models.CharField(max_length=255, blank=True)
    avoid_palette = models.CharField(max_length=255, blank=True)
    style_goal = models.TextField(blank=True)
    wardrobe_notes = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="DRAFT")
    style_identity = models.CharField(max_length=255, blank=True)
    body_summary = models.TextField(blank=True)
    outfit_direction = models.TextField(blank=True)
    wardrobe_blueprint = models.JSONField(default=list, blank=True)
    accessory_focus = models.TextField(blank=True)
    color_story = models.TextField(blank=True)
    confidence_notes = models.TextField(blank=True)
    visualization_prompt = models.TextField(blank=True)
    openrouter_provider = models.CharField(max_length=50, blank=True)
    openrouter_model = models.CharField(max_length=100, blank=True)
    raw_agent_response = models.JSONField(default=dict, blank=True)
    styleboard_project = models.ForeignKey(
        TangredProject,
        on_delete=models.SET_NULL,
        related_name="agent_sessions",
        null=True,
        blank=True,
    )
    styleboard_screen = models.ForeignKey(
        "TangredScreen",
        on_delete=models.SET_NULL,
        related_name="agent_sessions",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-modified_at"]

    def __str__(self):
        return self.title

    @property
    def photo_count(self):
        return self.photos.count()


class TangredSessionPhoto(models.Model):
    STORAGE_CHOICES = [
        ("local", "Local"),
        ("database", "Database"),
        ("firebase", "Firebase Storage"),
    ]

    session = models.ForeignKey(TangredSession, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="tangred/sessions/", blank=True, null=True)
    storage_backend = models.CharField(max_length=20, choices=STORAGE_CHOICES, default="database")
    storage_path = models.CharField(max_length=512, blank=True)
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=120, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    binary_content = models.BinaryField(blank=True, null=True)
    caption = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.caption or f"Photo for {self.session.title}"

    @property
    def access_url(self):
        return reverse("tangred_session_photo", args=[self.pk])


class TangredScreen(models.Model):
    DEVICE_CHOICES = [
        ("MOBILE", "Mobile"),
        ("DESKTOP", "Desktop"),
        ("TABLET", "Tablet"),
        ("AGNOSTIC", "Agnostic"),
    ]
    MODEL_CHOICES = [
        ("GEMINI_3_FLASH", "Gemini 3 Flash"),
        ("GEMINI_3_1_PRO", "Gemini 3.1 Pro"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(TangredProject, on_delete=models.CASCADE, related_name="screens")
    title = models.CharField(max_length=255, blank=True)
    prompt = models.TextField()
    optimized_prompt = models.TextField(blank=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_CHOICES, default="MOBILE")
    model_id = models.CharField(max_length=30, choices=MODEL_CHOICES, default="GEMINI_3_FLASH")
    prompt_optimizer_provider = models.CharField(max_length=50, blank=True)
    prompt_optimizer_model = models.CharField(max_length=100, blank=True)
    stitch_session_id = models.CharField(max_length=64, blank=True)
    stitch_screen_name = models.CharField(max_length=255, blank=True)
    stitch_screen_id = models.CharField(max_length=64, blank=True)
    screenshot_url = models.URLField(blank=True)
    html_url = models.URLField(blank=True)
    summary = models.TextField(blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=32, default="UNKNOWN")
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Tan Studio Screen {self.created_at:%Y-%m-%d %H:%M}"
