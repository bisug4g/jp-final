"""
Send scheduled push notifications
Usage: python manage.py send_notifications
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.services.push_notifications import PushNotificationService
from core.models_notifications import NotificationSchedule
import pytz


class Command(BaseCommand):
    help = 'Send scheduled push notifications'

    def handle(self, *args, **options):
        now = timezone.now()
        
        for schedule in NotificationSchedule.objects.filter(enabled=True):
            user_tz = pytz.timezone(schedule.timezone)
            user_time = now.astimezone(user_tz)
            
            current_time = user_time.time()
            morning_time = schedule.morning_time
            evening_time = schedule.evening_time
            
            # Check if it's morning reminder time (within 5 minutes)
            if abs((current_time.hour * 60 + current_time.minute) - 
                   (morning_time.hour * 60 + morning_time.minute)) <= 5:
                PushNotificationService.send_morning_reminder(schedule.user)
                self.stdout.write(f'Sent morning reminder to {schedule.user.username}')
            
            # Check if it's evening reminder time
            if schedule.evening_reminder:
                if abs((current_time.hour * 60 + current_time.minute) - 
                       (evening_time.hour * 60 + evening_time.minute)) <= 5:
                    PushNotificationService.send_evening_reminder(schedule.user)
                    self.stdout.write(f'Sent evening reminder to {schedule.user.username}')
