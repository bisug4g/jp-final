from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
import json
import random
from .models import DiaryEntry, DiaryPrompt


@login_required
def diary_overview(request):
    """Overview of diary entries"""
    entries = DiaryEntry.objects.filter(user=request.user)[:30]
    recent_entries = entries[:7]
    
    # Get streak
    streak = calculate_streak(request.user)
    
    context = {
        'entries': entries,
        'recent_entries': recent_entries,
        'streak': streak,
        'total_entries': DiaryEntry.objects.filter(user=request.user).count(),
    }
    return render(request, 'diary/diary_overview.html', context)


def calculate_streak(user):
    """Calculate current writing streak (consecutive days ending today or yesterday)"""
    dates = set(
        DiaryEntry.objects.filter(user=user)
        .values_list('entry_date', flat=True)
    )
    if not dates:
        return 0
    
    today = timezone.now().date()
    # Start from today; if no entry today, try yesterday
    check_date = today
    if check_date not in dates:
        check_date = today - timedelta(days=1)
        if check_date not in dates:
            return 0
    
    streak = 0
    while check_date in dates:
        streak += 1
        check_date -= timedelta(days=1)
    
    return streak


@login_required
def diary_write(request, date=None):
    """Write or edit diary entry - ONLY for current date"""
    today = timezone.now().date()
    
    # Parse date if provided
    if date:
        try:
            entry_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('diary_write')
    else:
        entry_date = today
    
    # STRICT: Only allow writing for current date
    if entry_date != today:
        messages.error(request, 'You can only write diary entries for today. Past entries are read-only.')
        return redirect('diary_overview')
    
    # Get or create entry
    entry, created = DiaryEntry.objects.get_or_create(
        user=request.user,
        entry_date=today,
        defaults={'input_method': 'type'}
    )
    
    # Get random prompt
    prompts = DiaryPrompt.objects.filter(is_active=True)
    if prompts:
        daily_prompt = random.choice(prompts)
    else:
        daily_prompt = None
    
    if request.method == 'POST':
        # Handle different input methods
        input_method = request.POST.get('input_method', 'type')
        entry.input_method = input_method
        
        if input_method == 'type':
            entry.content = request.POST.get('content', '')
            entry.content_html = request.POST.get('content_html', '')
        elif input_method == 'voice':
            entry.voice_transcript = request.POST.get('voice_transcript', '')
            entry.content = entry.voice_transcript
            if request.POST.get('voice_duration'):
                try:
                    entry.voice_duration = int(request.POST.get('voice_duration'))
                except (ValueError, TypeError):
                    pass
        elif input_method == 'stylus':
            try:
                entry.handwriting_strokes = json.loads(request.POST.get('handwriting_strokes', '[]'))
            except (json.JSONDecodeError, TypeError):
                entry.handwriting_strokes = []
            entry.handwriting_ocr_text = request.POST.get('handwriting_ocr_text', '')
            entry.content = entry.handwriting_ocr_text
        
        # Mood tracking
        mood = request.POST.get('mood')
        if mood:
            try:
                entry.mood = int(mood)
            except (ValueError, TypeError):
                pass
        entry.mood_note = request.POST.get('mood_note', '')
        
        # Prompt
        if request.POST.get('prompt_used'):
            entry.prompt_used = request.POST.get('prompt_used')
        
        entry.save()
        
        # Track activity
        try:
            from core.services.activity_tracker import record_diary_entry
            record_diary_entry(request.user)
        except Exception:
            pass
        
        messages.success(request, 'Diary entry saved. Thank you for taking this time for yourself.')
        return redirect('diary_entry_detail', pk=entry.pk)
    
    context = {
        'entry': entry,
        'today': today,
        'daily_prompt': daily_prompt,
        'is_editable': True,
    }
    return render(request, 'diary/diary_write.html', context)


@login_required
def diary_entry_detail(request, pk):
    """View a diary entry"""
    entry = get_object_or_404(DiaryEntry, pk=pk, user=request.user)
    today = timezone.now().date()
    
    context = {
        'entry': entry,
        'is_editable': entry.entry_date == today,
        'today': today,
    }
    return render(request, 'diary/diary_entry_detail.html', context)


@login_required
def diary_calendar(request):
    """Calendar view of diary entries"""
    today = timezone.now().date()
    
    # Get current month
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    
    # Get entries for this month
    from calendar import monthrange, Calendar
    first_day, days_in_month = monthrange(year, month)
    
    start_date = datetime(year, month, 1).date()
    end_date = datetime(year, month, days_in_month).date()
    
    entries = DiaryEntry.objects.filter(
        user=request.user,
        entry_date__range=[start_date, end_date]
    )
    
    entry_dates = {e.entry_date: e for e in entries}
    calendar_weeks = []
    calendar_helper = Calendar(firstweekday=6)
    for week in calendar_helper.monthdatescalendar(year, month):
        week_cells = []
        for week_date in week:
            week_cells.append({
                'date': week_date,
                'entry': entry_dates.get(week_date),
                'in_month': week_date.month == month,
            })
        calendar_weeks.append(week_cells)

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    
    context = {
        'year': year,
        'month': month,
        'month_name': datetime(year, month, 1).strftime('%B'),
        'days_in_month': days_in_month,
        'first_day': first_day,
        'entry_dates': entry_dates,
        'calendar_weeks': calendar_weeks,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'today': today,
    }
    return render(request, 'diary/diary_calendar.html', context)


@login_required
def diary_summary(request):
    """Weekly and monthly summaries"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Weekly stats
    week_entries = DiaryEntry.objects.filter(
        user=request.user,
        entry_date__gte=week_ago
    )
    
    # Monthly stats
    month_entries = DiaryEntry.objects.filter(
        user=request.user,
        entry_date__gte=month_ago
    )
    
    # Mood analysis
    week_moods = [e.mood for e in week_entries if e.mood]
    avg_mood = sum(week_moods) / len(week_moods) if week_moods else None
    
    context = {
        'week_entries': week_entries,
        'month_entries': month_entries,
        'week_count': week_entries.count(),
        'month_count': month_entries.count(),
        'avg_mood': avg_mood,
        'streak': calculate_streak(request.user),
    }
    return render(request, 'diary/diary_summary.html', context)
