"""
Web Push Notification Service
"""
from pywebpush import webpush, WebPushException
from django.conf import settings
import json


class PushNotificationService:
    """Send web push notifications"""
    
    @staticmethod
    def send_notification(subscription_info, message_data):
        """
        Send push notification to a subscription
        
        Args:
            subscription_info: Dict with endpoint and keys
            message_data: Dict with title, body, url
        """
        try:
            vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
            vapid_claims = {
                "sub": f"mailto:{getattr(settings, 'VAPID_ADMIN_EMAIL', 'admin@jaytibirthday.in')}"
            }
            
            if not vapid_private_key:
                print("VAPID keys not configured")
                return False
            
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(message_data),
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims
            )
            return True
            
        except WebPushException as e:
            print(f"Push notification failed: {e}")
            if e.response and e.response.status_code == 410:
                return 'expired'
            return False
    
    @staticmethod
    def send_morning_reminder(user):
        """Send morning diary reminder"""
        from core.models_notifications import PushSubscription
        
        subscriptions = PushSubscription.objects.filter(user=user, is_active=True)
        
        message = {
            'title': 'Good morning, Jayti! ☀️',
            'body': 'Your diary is waiting for you. Take a moment to reflect on your day.',
            'url': '/diary/write/'
        }
        
        for sub in subscriptions:
            result = PushNotificationService.send_notification(
                sub.get_subscription_info(),
                message
            )
            if result == 'expired':
                sub.is_active = False
                sub.save()
    
    @staticmethod
    def send_evening_reminder(user):
        """Send evening diary reminder"""
        from core.models_notifications import PushSubscription
        
        subscriptions = PushSubscription.objects.filter(user=user, is_active=True)
        
        message = {
            'title': 'Evening reflection time 🌙',
            'body': 'How was your day? Write about it before you sleep.',
            'url': '/diary/write/'
        }
        
        for sub in subscriptions:
            result = PushNotificationService.send_notification(
                sub.get_subscription_info(),
                message
            )
            if result == 'expired':
                sub.is_active = False
                sub.save()
