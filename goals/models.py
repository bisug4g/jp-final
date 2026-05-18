from django.db import models
from django.contrib.auth.models import User
import uuid


class Goal(models.Model):
    """High-level goals with time horizons"""
    TIME_HORIZONS = [
        ('1year', '1 Year'),
        ('3year', '3 Years'),
        ('5year', '5 Years'),
        ('10year', '10 Years'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    
    # Career framework
    role_category = models.CharField(max_length=50, choices=[
        ('digital_marketing', 'Digital Marketing'),
        ('brand_management', 'Brand Management'),
        ('content_strategy', 'Content Strategy'),
        ('market_research', 'Market Research'),
        ('product_marketing', 'Product Marketing'),
        ('social_media', 'Social Media'),
        ('seo_sem', 'SEO/SEM'),
        ('marketing_analytics', 'Marketing Analytics'),
    ])
    
    experience_level = models.CharField(max_length=20, choices=[
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('leadership', 'Leadership'),
    ])
    
    time_horizon = models.CharField(max_length=10, choices=TIME_HORIZONS)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    completion_percentage = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Task(models.Model):
    """Tasks linked to goals"""
    DEPARTMENTS = [
        ('finance', 'Finance'),
        ('hr', 'HR'),
        ('sales', 'Sales'),
        ('operations', 'Operations'),
        ('strategy', 'Strategy'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('blocked', 'Blocked'),
        ('at_risk', 'At Risk'),
        ('overdue', 'Overdue'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='tasks')
    
    # Corporate simulation
    department = models.CharField(max_length=20, choices=DEPARTMENTS, default='strategy')
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Temporal structure
    is_quarterly = models.BooleanField(default=False)
    is_monthly = models.BooleanField(default=False)
    is_weekly = models.BooleanField(default=False)
    is_daily = models.BooleanField(default=False)
    
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completion_percentage = models.IntegerField(default=0)
    
    # Tracking
    blocked_reason = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date', 'created_at']
    
    def __str__(self):
        return self.title


class Milestone(models.Model):
    """Key milestones within goals"""
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    is_achieved = models.BooleanField(default=False)
    achieved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['target_date']
    
    def __str__(self):
        return self.title
