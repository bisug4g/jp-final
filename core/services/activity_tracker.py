"""
Activity Tracker Service
Tracks and aggregates user engagement from Feb 6, 2026 onwards
With caching for performance
"""
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count
from django.core.cache import cache
from core.models import DailyActivity
from notes.models import Note
from diary.models import DiaryEntry
from goals.models import Goal, Task
import pytz


# Start tracking from Jayti's birthday 2026
TRACKING_START_DATE = date(2026, 2, 6)


def get_or_create_daily_activity(user, activity_date=None):
    """Get or create daily activity record"""
    if activity_date is None:
        ist_tz = pytz.timezone('Asia/Kolkata')
        activity_date = timezone.now().astimezone(ist_tz).date()
    
    activity, created = DailyActivity.objects.get_or_create(
        user=user,
        date=activity_date
    )
    return activity


def record_login(user):
    """Record a login event"""
    activity = get_or_create_daily_activity(user)
    activity.login_count += 1
    if not activity.first_activity:
        activity.first_activity = timezone.now()
    activity.last_activity = timezone.now()
    activity.save()


def record_note_created(user):
    """Record note creation"""
    activity = get_or_create_daily_activity(user)
    activity.notes_created += 1
    activity.last_activity = timezone.now()
    activity.save()


def record_note_edited(user):
    """Record note edit"""
    activity = get_or_create_daily_activity(user)
    activity.notes_edited += 1
    activity.last_activity = timezone.now()
    activity.save()


def record_diary_entry(user):
    """Record diary entry"""
    activity = get_or_create_daily_activity(user)
    activity.diary_entries += 1
    activity.last_activity = timezone.now()
    activity.save()


def record_goal_created(user):
    """Record goal creation"""
    activity = get_or_create_daily_activity(user)
    activity.goals_created += 1
    activity.last_activity = timezone.now()
    activity.save()


def record_task_completed(user):
    """Record task completion"""
    activity = get_or_create_daily_activity(user)
    activity.tasks_completed += 1
    activity.last_activity = timezone.now()
    activity.save()


def record_ai_chat(user):
    """Record AI chat interaction"""
    activity = get_or_create_daily_activity(user)
    activity.ai_chats += 1
    activity.last_activity = timezone.now()
    activity.save()


def calculate_historical_activity(user):
    """
    Calculate activity from historical data for dates without activity records.
    This fills in gaps from Feb 6, 2026 to today based on created_at timestamps.
    Cached to avoid recalculating on every request.
    """
    # Check if we've already calculated today
    cache_key = f"historical_activity_calculated_{user.id}_{timezone.now().strftime('%Y%m%d')}"
    if cache.get(cache_key):
        return  # Already calculated today
    
    ist_tz = pytz.timezone('Asia/Kolkata')
    today = timezone.now().astimezone(ist_tz).date()
    
    # Only process dates from tracking start
    if today < TRACKING_START_DATE:
        return
    
    # Get existing activity dates
    existing_dates = set(
        DailyActivity.objects.filter(user=user)
        .values_list('date', flat=True)
    )
    
    # Calculate notes per day
    notes_by_date = {}
    for note in Note.objects.filter(user=user, created_at__date__gte=TRACKING_START_DATE):
        note_date = note.created_at.astimezone(ist_tz).date()
        if note_date not in notes_by_date:
            notes_by_date[note_date] = {'created': 0, 'edited': 0}
        notes_by_date[note_date]['created'] += 1
    
    # Track edits (modified != created means edit)
    for note in Note.objects.filter(user=user, modified_at__date__gte=TRACKING_START_DATE):
        note_date = note.modified_at.astimezone(ist_tz).date()
        if note.modified_at != note.created_at:
            if note_date not in notes_by_date:
                notes_by_date[note_date] = {'created': 0, 'edited': 0}
            notes_by_date[note_date]['edited'] += 1
    
    # Calculate diary entries per day
    diary_by_date = {}
    for entry in DiaryEntry.objects.filter(user=user, entry_date__gte=TRACKING_START_DATE):
        if entry.entry_date not in diary_by_date:
            diary_by_date[entry.entry_date] = 0
        diary_by_date[entry.entry_date] += 1
    
    # Calculate goals per day
    goals_by_date = {}
    for goal in Goal.objects.filter(user=user, created_at__date__gte=TRACKING_START_DATE):
        goal_date = goal.created_at.astimezone(ist_tz).date()
        if goal_date not in goals_by_date:
            goals_by_date[goal_date] = 0
        goals_by_date[goal_date] += 1
    
    # Calculate tasks completed per day
    tasks_by_date = {}
    for task in Task.objects.filter(
        goal__user=user, 
        status='done',
        completed_at__date__gte=TRACKING_START_DATE
    ):
        if task.completed_at:
            task_date = task.completed_at.astimezone(ist_tz).date()
            if task_date not in tasks_by_date:
                tasks_by_date[task_date] = 0
            tasks_by_date[task_date] += 1
    
    # Merge all dates
    all_dates = set(notes_by_date.keys()) | set(diary_by_date.keys()) | set(goals_by_date.keys()) | set(tasks_by_date.keys())
    
    # Create activity records
    for activity_date in all_dates:
        if activity_date not in existing_dates and activity_date >= TRACKING_START_DATE:
            notes_data = notes_by_date.get(activity_date, {'created': 0, 'edited': 0})
            DailyActivity.objects.create(
                user=user,
                date=activity_date,
                notes_created=notes_data['created'],
                notes_edited=notes_data['edited'],
                diary_entries=diary_by_date.get(activity_date, 0),
                goals_created=goals_by_date.get(activity_date, 0),
                tasks_completed=tasks_by_date.get(activity_date, 0),
            )
    
    # Mark as calculated for today (cache for 1 hour)
    cache.set(cache_key, True, 60 * 60)


def get_activity_calendar(user, year=None, month=None):
    """
    Get activity data for calendar display.
    Returns all days from Feb 6, 2026 to today with activity status.
    Cached for 10 minutes to improve performance.
    """
    # Check cache first
    cache_key = f"activity_calendar_{user.id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    ist_tz = pytz.timezone('Asia/Kolkata')
    today = timezone.now().astimezone(ist_tz).date()
    
    # Ensure historical data is calculated
    calculate_historical_activity(user)
    
    # Get all activity records
    activities = DailyActivity.objects.filter(
        user=user,
        date__gte=TRACKING_START_DATE,
        date__lte=today
    ).order_by('date')
    
    activity_dict = {a.date: a for a in activities}
    
    # Build calendar data from Feb 6, 2026 to today
    calendar_data = []
    current_date = TRACKING_START_DATE
    
    while current_date <= today:
        activity = activity_dict.get(current_date)
        
        day_data = {
            'date': current_date.isoformat(),
            'day': current_date.day,
            'month': current_date.month,
            'year': current_date.year,
            'weekday': current_date.weekday(),  # 0=Monday, 6=Sunday
            'has_activity': False,
            'activity_score': 0,
            'details': {
                'notes': 0,
                'diary': 0,
                'goals': 0,
                'tasks': 0,
                'chats': 0,
                'logins': 0
            }
        }
        
        if activity:
            day_data['has_activity'] = activity.has_activity
            day_data['activity_score'] = activity.activity_score
            day_data['details'] = {
                'notes': activity.notes_created + activity.notes_edited,
                'diary': activity.diary_entries,
                'goals': activity.goals_created,
                'tasks': activity.tasks_completed,
                'chats': activity.ai_chats,
                'logins': activity.login_count
            }
        
        calendar_data.append(day_data)
        current_date += timedelta(days=1)
    
    # Cache for 10 minutes
    cache.set(cache_key, calendar_data, 60 * 10)
    
    return calendar_data


def get_activity_stats(user):
    """Get overall activity statistics"""
    ist_tz = pytz.timezone('Asia/Kolkata')
    today = timezone.now().astimezone(ist_tz).date()
    
    # Ensure historical data is calculated
    calculate_historical_activity(user)
    
    total_days = (today - TRACKING_START_DATE).days + 1
    
    activities = DailyActivity.objects.filter(
        user=user,
        date__gte=TRACKING_START_DATE,
        date__lte=today
    )
    
    # Count active days
    active_days = sum(1 for a in activities if a.has_activity)
    inactive_days = total_days - active_days
    
    # Calculate totals
    totals = activities.aggregate(
        total_notes=Sum('notes_created'),
        total_diary=Sum('diary_entries'),
        total_goals=Sum('goals_created'),
        total_tasks=Sum('tasks_completed'),
        total_chats=Sum('ai_chats'),
        total_logins=Sum('login_count')
    )
    
    # Calculate streak (consecutive active days ending today or yesterday)
    current_streak = 0
    check_date = today
    
    while check_date >= TRACKING_START_DATE:
        activity = activities.filter(date=check_date).first()
        if activity and activity.has_activity:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    # Calculate longest streak
    longest_streak = 0
    temp_streak = 0
    
    for single_date in (TRACKING_START_DATE + timedelta(n) for n in range(total_days)):
        activity = activities.filter(date=single_date).first()
        if activity and activity.has_activity:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0
    
    return {
        'tracking_start': TRACKING_START_DATE.isoformat(),
        'total_days': total_days,
        'active_days': active_days,
        'inactive_days': inactive_days,
        'engagement_rate': round((active_days / total_days) * 100, 1) if total_days > 0 else 0,
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'totals': {
            'notes': totals['total_notes'] or 0,
            'diary': totals['total_diary'] or 0,
            'goals': totals['total_goals'] or 0,
            'tasks': totals['total_tasks'] or 0,
            'chats': totals['total_chats'] or 0,
            'logins': totals['total_logins'] or 0
        }
    }
