import random
import hashlib
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
import pytz
from .models import DailyThought, UserProfile


def get_daily_content():
    """Get daily thought and content based on date"""
    today = datetime.now()
    date_seed = today.strftime('%Y%m%d')
    
    # Calculate hash value once for consistent daily selection
    hash_val = int(hashlib.md5(date_seed.encode()).hexdigest(), 16)
    
    # Get all active thoughts
    thoughts = list(DailyThought.objects.filter(is_active=True))
    
    if thoughts:
        # Use date-based hash for consistent daily selection
        thought = thoughts[hash_val % len(thoughts)]
    else:
        # Default thoughts if none in database (25 quotes for variety)
        default_thoughts = [
            {"content": "The lotus blooms most beautifully from the deepest and thickest mud.", "author": "Buddhist Proverb"},
            {"content": "Your strength is not measured by how much you can carry, but by how you rise after being broken.", "author": "Unknown"},
            {"content": "Every ending is a new beginning. Trust the journey.", "author": "Unknown"},
            {"content": "You are stronger than you know, more capable than you imagine, and loved more than you realize.", "author": "Unknown"},
            {"content": "The path to healing begins with a single breath of self-compassion.", "author": "Unknown"},
            {"content": "Courage doesn't always roar. Sometimes courage is the quiet voice at the end of the day saying, 'I will try again tomorrow.'", "author": "Mary Anne Radmacher"},
            {"content": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
            {"content": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill"},
            {"content": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
            {"content": "Your present circumstances don't determine where you go; they merely determine where you start.", "author": "Nido Qubein"},
            {"content": "Be gentle with yourself. You're doing the best you can.", "author": "Unknown"},
            {"content": "In the middle of difficulty lies opportunity.", "author": "Albert Einstein"},
            {"content": "The best time to plant a tree was 20 years ago. The second best time is now.", "author": "Chinese Proverb"},
            {"content": "You are allowed to be both a masterpiece and a work in progress simultaneously.", "author": "Sophia Bush"},
            {"content": "Don't watch the clock; do what it does. Keep going.", "author": "Sam Levenson"},
            {"content": "The flower that blooms in adversity is the most rare and beautiful of all.", "author": "Mulan"},
            {"content": "You don't have to be perfect to be amazing.", "author": "Unknown"},
            {"content": "Difficult roads often lead to beautiful destinations.", "author": "Unknown"},
            {"content": "Small steps in the right direction can turn out to be the biggest step of your life.", "author": "Unknown"},
            {"content": "Your value doesn't decrease based on someone's inability to see your worth.", "author": "Unknown"},
            {"content": "Champions keep playing until they get it right.", "author": "Billie Jean King"},
            {"content": "Fall seven times, stand up eight.", "author": "Japanese Proverb"},
            {"content": "The only person you are destined to become is the person you decide to be.", "author": "Ralph Waldo Emerson"},
            {"content": "Progress, not perfection.", "author": "Unknown"},
            {"content": "Success usually comes to those who are too busy to be looking for it.", "author": "Henry David Thoreau"},
        ]
        thought_data = default_thoughts[hash_val % len(default_thoughts)]
        thought = type('obj', (object,), {
            'content': thought_data['content'],
            'author': thought_data['author'],
            'category': 'resilience'
        })
    
    return {
        'thought': thought,
        'date': today,
    }


def get_birthday_countdown():
    """Calculate days until Jayti's birthday (Feb 6)"""
    ist_tz = pytz.timezone('Asia/Kolkata')
    now_utc = timezone.now()
    today_ist = now_utc.astimezone(ist_tz)
    
    current_year = today_ist.year
    birthday_this_year = datetime(current_year, 2, 6, tzinfo=ist_tz)
    birthday_next_year = datetime(current_year + 1, 2, 6, tzinfo=ist_tz)
    
    # Determine next birthday
    if today_ist.month == 2 and today_ist.day == 6:
        # It's her birthday!
        return {
            'days_until': 0,
            'is_today': True,
            'is_tomorrow': False,
            'next_birthday': birthday_this_year,
            'age_on_next_birthday': current_year - 1997
        }
    elif today_ist < birthday_this_year.replace(tzinfo=ist_tz):
        # Birthday hasn't happened yet this year
        next_birthday = birthday_this_year
        days_until = (next_birthday.replace(tzinfo=None) - today_ist.replace(tzinfo=None)).days
    else:
        # Birthday already passed this year
        next_birthday = birthday_next_year
        days_until = (next_birthday.replace(tzinfo=None) - today_ist.replace(tzinfo=None)).days
    
    return {
        'days_until': days_until,
        'is_today': False,
        'is_tomorrow': days_until == 1,
        'next_birthday': next_birthday,
        'age_on_next_birthday': next_birthday.year - 1997
    }


def get_time_greeting():
    """Get time-appropriate greeting"""
    hour = datetime.now().hour
    if 5 <= hour < 11:
        return {
            'greeting': 'Good Morning',
            'theme': 'morning',
            'message': 'New beginnings await. Take a breath and begin.',
        }
    elif 11 <= hour < 17:
        return {
            'greeting': 'Good Afternoon',
            'theme': 'afternoon',
            'message': 'Persistence creates progress. You are doing well.',
        }
    elif 17 <= hour < 22:
        return {
            'greeting': 'Good Evening',
            'theme': 'evening',
            'message': 'Reflect on your day with kindness.',
        }
    else:
        return {
            'greeting': 'Good Night',
            'theme': 'night',
            'message': 'Rest is restoration. Tomorrow brings new light.',
        }


def login_view(request):
    """Custom login view with daily content and birthday recognition"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    error = None
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Record login activity
            try:
                from core.services.activity_tracker import record_login
                from core.models import UserSession
                import user_agents as ua_parser
                ua_string = request.META.get('HTTP_USER_AGENT', '')
                ua = ua_parser.parse(ua_string)
                x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR', '')
                device_type = 'mobile' if ua.is_mobile else 'tablet' if ua.is_tablet else 'desktop'
                UserSession.objects.update_or_create(
                    user=user,
                    ip_address=ip,
                    defaults={
                        'user_agent': ua_string,
                        'device_type': device_type,
                        'browser': ua.browser.family,
                        'os': ua.os.family,
                        'is_active': True
                    }
                )
                record_login(user)
            except Exception:
                pass  # Don't block login if tracking fails
            return redirect('dashboard')
        else:
            error = "Invalid credentials. Please try again."
    
    context = {
        'daily_content': get_daily_content(),
        'time_context': get_time_greeting(),
        'error': error,
        'is_birthday': datetime.now().day == 6 and datetime.now().month == 2,
    }
    
    return render(request, 'core/login.html', context)


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard with navigation to all modules"""
    from notes.models import Note
    from diary.models import DiaryEntry
    from goals.models import Goal, Task
    from datetime import datetime
    from django.db.models import Count, Q
    
    # Single aggregation query for all counts
    user = request.user
    stats = {
        'recent_notes': Note.objects.filter(user=user).count(),
        'recent_diary': DiaryEntry.objects.filter(user=user).count(),
        'active_goals': Goal.objects.filter(user=user, status='active').count(),
        'pending_tasks': Task.objects.filter(goal__user=user, status='pending').count(),
    }
    
    # Check if today is February 6 (Jayti's Birthday) in Indian Standard Time (IST)
    now_utc = timezone.now()
    ist_tz = pytz.timezone('Asia/Kolkata')
    today_ist = now_utc.astimezone(ist_tz)
    
    is_birthday = (today_ist.month == 2 and today_ist.day == 6)
    jayti_age = today_ist.year - 1997
    show_vivek_message = is_birthday
    show_weekly_summary = (today_ist.weekday() == 6)
    
    # Get birthday countdown data
    birthday_countdown = get_birthday_countdown()
    
    context = {
        'recent_notes': stats['recent_notes'],
        'recent_diary': stats['recent_diary'],
        'active_goals': stats['active_goals'],
        'pending_tasks': stats['pending_tasks'],
        'show_vivek_message': show_vivek_message,
        'is_birthday': is_birthday,
        'jayti_age': jayti_age,
        'show_weekly_summary': show_weekly_summary,
        'birthday_countdown': birthday_countdown,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def profile(request):
    """User profile view"""
    if request.method == 'POST':
        profile = request.user.profile
        profile.display_name = request.POST.get('display_name', profile.display_name)
        profile.preferred_language = request.POST.get('preferred_language', profile.preferred_language)
        notification_time = request.POST.get('notification_time')
        if notification_time:
            profile.notification_time = notification_time
        
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    
    return render(request, 'core/profile.html')


@login_required
def password_change_view(request):
    """Password change view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'core/password_change.html', {'form': form})


@require_POST
def birthday_seen(request):
    """Mark birthday message as seen - no login required since shown on login page"""
    try:
        if request.user.is_authenticated:
            profile = request.user.profile
            profile.birthday_message_seen_2026 = True
            profile.save()
        return JsonResponse({'success': True})
    except:
        return JsonResponse({'success': True})


def health_check(request):
    """
    Health check endpoint for deployment.
    Returns 200 OK immediately - CRITICAL for Kubernetes probes.
    This must be extremely lightweight - no database, no imports.
    """
    import json
    from datetime import datetime
    from django.http import HttpResponse
    
    # Return 200 immediately - server is alive
    health_data = json.dumps({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    })
    
    return HttpResponse(health_data, content_type='application/json', status=200)



@login_required
def session_dashboard(request):
    """
    Dashboard to view all login sessions with IP and device information.
    Only accessible to the user viewing their own sessions (for privacy).
    """
    from .models import UserSession
    from collections import defaultdict
    
    # Get all tracked sessions for this user
    sessions = UserSession.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate statistics
    total_sessions = sessions.count()
    active_sessions = sessions.filter(is_active=True).count()
    
    # Get unique IPs
    unique_ips = sessions.exclude(ip_address=None).values_list('ip_address', flat=True).distinct()
    
    # Get unique devices by user agent
    unique_devices = sessions.values_list('user_agent', flat=True).distinct()
    
    # Group by device type
    device_stats = defaultdict(int)
    for session in sessions:
        device_stats[session.device_type] += 1
    
    # Group by browser
    browser_stats = defaultdict(int)
    for session in sessions:
        if session.browser:
            browser_stats[session.browser] += 1
    
    # Group by OS
    os_stats = defaultdict(int)
    for session in sessions:
        if session.os:
            os_stats[session.os] += 1
    
    # Recent sessions (last 10)
    recent_sessions = sessions[:10]
    
    # Active sessions
    current_sessions = sessions.filter(is_active=True)[:10]
    
    # Suspicious sessions
    suspicious_sessions = [s for s in sessions if s.is_suspicious][:10]
    
    context = {
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'unique_ip_count': len(unique_ips),
        'unique_device_count': len(unique_devices),
        'device_stats': dict(device_stats),
        'browser_stats': dict(browser_stats),
        'os_stats': dict(os_stats),
        'recent_sessions': recent_sessions,
        'current_sessions': current_sessions,
        'suspicious_sessions': suspicious_sessions,
        'unique_ips': unique_ips[:20],
    }
    
    return render(request, 'core/session_dashboard.html', context)


@login_required
@require_POST
def terminate_session(request, session_id):
    """Terminate a specific session (log out from that device)"""
    from .models import UserSession
    from django.contrib.sessions.models import Session as DjangoSession
    
    try:
        user_session = UserSession.objects.get(id=session_id, user=request.user)
        
        # Delete the Django session
        try:
            DjangoSession.objects.filter(session_key=user_session.session_key).delete()
        except:
            pass
        
        # Mark as inactive
        user_session.is_active = False
        user_session.save()
        
        messages.success(request, 'Session terminated successfully.')
    except UserSession.DoesNotExist:
        messages.error(request, 'Session not found.')
    
    return redirect('session_dashboard')
