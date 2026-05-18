from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class DiaryEntry(models.Model):
    """Diary entries with multi-modal input"""
    INPUT_METHODS = [
        ('type', 'Typing'),
        ('voice', 'Voice'),
        ('stylus', 'Stylus/Handwriting'),
    ]
    
    MOOD_CHOICES = [
        (1, '😔 Struggling'),
        (2, '😕 Difficult'),
        (3, '😐 Neutral'),
        (4, '🙂 Good'),
        (5, '😊 Great'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diary_entries')
    entry_date = models.DateField()
    
    # Content
    content = models.TextField(blank=True)  # Typed content
    content_html = models.TextField(blank=True)  # HTML formatted content
    
    # Input method
    input_method = models.CharField(max_length=10, choices=INPUT_METHODS, default='type')
    
    # Voice data
    voice_transcript = models.TextField(blank=True)
    voice_duration = models.IntegerField(null=True, blank=True)  # seconds
    
    # Handwriting data (JSON for stroke data)
    handwriting_strokes = models.JSONField(null=True, blank=True)
    handwriting_ocr_text = models.TextField(blank=True)
    handwriting_image = models.ImageField(upload_to='diary/handwriting/', blank=True, null=True)
    
    # Mood tracking
    mood = models.IntegerField(choices=MOOD_CHOICES, null=True, blank=True)
    mood_note = models.CharField(max_length=200, blank=True)
    
    # Prompt response
    prompt_used = models.CharField(max_length=300, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-entry_date']
        unique_together = ['user', 'entry_date']
        verbose_name_plural = 'Diary Entries'
        indexes = [
            models.Index(fields=['user', '-entry_date']),
        ]
    
    def __str__(self):
        return f"Diary Entry - {self.entry_date}"
    
    @property
    def is_editable(self):
        """Check if entry is editable (only current date)"""
        return self.entry_date == timezone.now().date()


class DiaryPrompt(models.Model):
    """Daily prompts for reflection"""
    CATEGORY_CHOICES = [
        ('self_awareness', 'Self-Awareness'),
        ('relationships', 'Relationships'),
        ('professional', 'Professional Growth'),
        ('gratitude', 'Gratitude'),
        ('challenges', 'Challenge Processing'),
        ('general', 'General'),
    ]
    
    question = models.CharField(max_length=300)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Diary Prompts'
    
    def __str__(self):
        return self.question[:50]


class MoodSummary(models.Model):
    """Aggregated mood data for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_summaries')
    week_start = models.DateField()
    avg_mood = models.FloatField()
    entry_count = models.IntegerField()
    dominant_theme = models.CharField(max_length=100, blank=True)
    
    class Meta:
        unique_together = ['user', 'week_start']
        verbose_name_plural = 'Mood Summaries'
