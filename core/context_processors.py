from django.utils import timezone
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
import hashlib
from .models import DailyThought


def user_profile(request):
    """Add user profile to context"""
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            return {
                'user_profile': profile,
                'display_name': profile.display_name,
            }
        except:
            pass
    return {}


def birthday_check(request):
    """Check if today is Jayti's birthday"""
    today = timezone.now()
    is_birthday = (today.day == settings.JAYTI_BIRTH_DATE and 
                   today.month == settings.JAYTI_BIRTH_MONTH)
    
    birthday_message_seen = False
    if request.user.is_authenticated:
        try:
            birthday_message_seen = request.user.profile.birthday_message_seen_2026
        except:
            pass
    
    return {
        'is_birthday': is_birthday,
        'birthday_message_seen': birthday_message_seen,
        'jayti_age': today.year - 1997,
    }


def daily_inspiration(request):
    """Add daily thought and greeting to context - with caching"""
    today = timezone.now()
    date_seed = today.strftime('%Y%m%d')
    
    # Cache key for daily thought
    cache_key = f'daily_thought_{date_seed}'
    thought = cache.get(cache_key)
    
    if thought is None:
        # Get daily thought from database
        thoughts = list(DailyThought.objects.filter(is_active=True))
        
        if thoughts:
            hash_val = int(hashlib.md5(date_seed.encode()).hexdigest(), 16)
            thought = thoughts[hash_val % len(thoughts)]
        else:
            # Default fallback thought
            thought = None
        
        # Cache for 1 hour
        cache.set(cache_key, thought, 60 * 60)
    
    # Time-based greeting (no DB query needed)
    hour = today.hour
    if 5 <= hour < 11:
        greeting = {
            'text': 'Good Morning',
            'theme': 'morning',
            'message': 'New beginnings await. Take a breath and begin.',
        }
    elif 11 <= hour < 17:
        greeting = {
            'text': 'Good Afternoon',
            'theme': 'afternoon',
            'message': 'Persistence creates progress. You are doing well.',
        }
    elif 17 <= hour < 22:
        greeting = {
            'text': 'Good Evening',
            'theme': 'evening',
            'message': 'Reflect on your day with kindness.',
        }
    else:
        greeting = {
            'text': 'Good Night',
            'theme': 'night',
            'message': 'Rest is restoration. Tomorrow brings new light.',
        }
    
    # Check if this is first login of the day (for Vivek's message)
    show_vivek_message = False
    if request.user.is_authenticated:
        try:
            last_login = request.user.profile.last_daily_greeting
            if not last_login or last_login.date() < today.date():
                show_vivek_message = True
                request.user.profile.last_daily_greeting = today
                request.user.profile.save()
        except:
            pass
    
    return {
        'daily_thought': thought,
        'time_greeting': greeting,
        'show_vivek_message': show_vivek_message,
        'current_date': today,
        'VAPID_PUBLIC_KEY': getattr(settings, 'VAPID_PUBLIC_KEY', ''),
    }




def firebase_config(request):
    """Expose public Firebase config to templates without hardcoding secrets."""
    return {
        'FIREBASE_CONFIG': {
            'enabled': getattr(settings, 'FIREBASE_ENABLED', False),
            'apiKey': getattr(settings, 'FIREBASE_API_KEY', ''),
            'authDomain': getattr(settings, 'FIREBASE_AUTH_DOMAIN', ''),
            'projectId': getattr(settings, 'FIREBASE_PROJECT_ID', ''),
            'storageBucket': getattr(settings, 'FIREBASE_STORAGE_BUCKET', ''),
            'messagingSenderId': getattr(settings, 'FIREBASE_MESSAGING_SENDER_ID', ''),
            'appId': getattr(settings, 'FIREBASE_APP_ID', ''),
            'measurementId': getattr(settings, 'FIREBASE_MEASUREMENT_ID', ''),
        }
    }
