from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile for Jyati"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=50, default='Jyati')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    preferred_language = models.CharField(max_length=10, default='en', choices=[
        ('en', 'English'),
        ('hi', 'हिन्दी'),
        ('he', 'Hinglish'),
    ])
    notification_enabled = models.BooleanField(default=True)
    notification_time = models.TimeField(default='09:00')
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    # Birthday message display tracking
    birthday_message_seen_2026 = models.BooleanField(default=False)
    
    # Daily greeting tracking
    last_daily_greeting = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.display_name}'s Profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class DailyThought(models.Model):
    """Curated daily thoughts for login page"""
    CATEGORY_CHOICES = [
        ('resilience', 'Resilience'),
        ('growth', 'Growth'),
        ('self_compassion', 'Self-Compassion'),
        ('professional', 'Professional Excellence'),
        ('relationships', 'Relationships'),
        ('spiritual', 'Spiritual Reflection'),
    ]
    
    content = models.TextField()
    author = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.category}: {self.content[:50]}..."


class DailyFlower(models.Model):
    """Seasonal flower images for login page"""
    SEASON_CHOICES = [
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('autumn', 'Autumn'),
        ('winter', 'Winter'),
    ]
    
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='flowers/')
    season = models.CharField(max_length=10, choices=SEASON_CHOICES)
    meaning = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class PushSubscription(models.Model):
    """Store web push subscriptions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'endpoint']
    
    def __str__(self):
        return f"Push subscription for {self.user.username}"
    
    def get_subscription_info(self):
        return {
            'endpoint': self.endpoint,
            'keys': {'p256dh': self.p256dh, 'auth': self.auth}
        }


class NotificationSchedule(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_schedule')
    enabled = models.BooleanField(default=True)
    morning_time = models.TimeField(default='09:00')
    evening_reminder = models.BooleanField(default=True)
    evening_time = models.TimeField(default='20:00')
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    
    def __str__(self):
        return f"Notification schedule for {self.user.username}"


class DailyActivity(models.Model):
    """Track daily user activity from Feb 6, 2026 onwards"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_activities')
    date = models.DateField()
    
    # Activity counts
    notes_created = models.IntegerField(default=0)
    notes_edited = models.IntegerField(default=0)
    diary_entries = models.IntegerField(default=0)
    goals_created = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    ai_chats = models.IntegerField(default=0)
    
    # Session info
    login_count = models.IntegerField(default=0)
    total_time_minutes = models.IntegerField(default=0)  # Estimated time spent
    
    # Timestamps
    first_activity = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        verbose_name_plural = 'Daily Activities'
    
    def __str__(self):
        return f"Activity for {self.user.username} on {self.date}"
    
    @property
    def has_activity(self):
        """Check if any activity was recorded"""
        return (
            self.notes_created > 0 or
            self.notes_edited > 0 or
            self.diary_entries > 0 or
            self.goals_created > 0 or
            self.tasks_completed > 0 or
            self.ai_chats > 0 or
            self.login_count > 0
        )
    
    @property
    def activity_score(self):
        """Calculate engagement score (0-100)"""
        score = 0
        score += min(self.notes_created * 15, 30)  # Max 30 for notes
        score += min(self.diary_entries * 25, 25)  # Max 25 for diary
        score += min(self.goals_created * 10, 20)  # Max 20 for goals
        score += min(self.tasks_completed * 5, 15)  # Max 15 for tasks
        score += min(self.ai_chats * 2, 10)  # Max 10 for chats
        return min(score, 100)


class UserSession(models.Model):
    """Track user login sessions with IP and device information"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tracked_sessions')
    session_key = models.CharField(max_length=40, unique=True)

    # IP Address information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    ip_city = models.CharField(max_length=100, blank=True)
    ip_country = models.CharField(max_length=100, blank=True)
    ip_region = models.CharField(max_length=100, blank=True)

    # Device information
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20, default='unknown', choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('bot', 'Bot'),
        ('unknown', 'Unknown'),
    ])
    browser = models.CharField(max_length=100, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=100, blank=True)
    os_version = models.CharField(max_length=50, blank=True)

    # Session timing
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'

    def __str__(self):
        return f"{self.user.username} - {self.ip_address} - {self.device_type}"

    @property
    def duration(self):
        """Calculate session duration"""
        if self.last_activity and self.created_at:
            diff = self.last_activity - self.created_at
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if diff.days > 0:
                return f"{diff.days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m {seconds}s"
        return "N/A"

    @property
    def device_icon(self):
        """Return appropriate icon class"""
        icons = {
            'desktop': '💻',
            'mobile': '📱',
            'tablet': '📲',
            'bot': '🤖',
            'unknown': '❓',
        }
        return icons.get(self.device_type, '❓')

    @property
    def is_suspicious(self):
        """Flag suspicious sessions"""
        # Flag if from known datacenter IP ranges or unusual patterns
        suspicious_countries = ['RU', 'CN', 'KP', 'IR']  # Example
        return self.ip_country in suspicious_countries or self.device_type == 'bot'


