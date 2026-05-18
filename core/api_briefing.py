from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from core.services.ai_runtime import AIConfigurationError, AIProviderError
from core.services.daily_briefing import get_daily_briefing
from core.services.weekly_summary import get_weekly_summary


def _daily_stats(user):
    from diary.models import DiaryEntry
    from goals.models import Goal, Task
    from notes.models import Note

    now = timezone.now()
    recent_notes = Note.objects.filter(user=user, created_at__gte=now - timedelta(days=7)).count()
    recent_diary = DiaryEntry.objects.filter(
        user=user,
        entry_date__gte=now.date() - timedelta(days=7),
    ).count()
    active_goals = Goal.objects.filter(user=user, status="active").count()
    pending_tasks = Task.objects.filter(
        goal__user=user,
        status__in=["pending", "in_progress", "blocked", "at_risk", "overdue"],
    ).count()

    return {
        "notes": recent_notes,
        "diary": recent_diary,
        "goals": active_goals,
        "tasks": pending_tasks,
    }


def _weekly_stats(user):
    from diary.models import DiaryEntry
    from goals.models import Task

    week_start = timezone.now().date() - timedelta(days=7)
    entries = DiaryEntry.objects.filter(user=user, entry_date__gte=week_start).order_by("entry_date")
    entries_count = entries.count()
    moods = [entry.mood for entry in entries if entry.mood]
    avg_mood = round(sum(moods) / len(moods), 1) if moods else None
    completed = Task.objects.filter(
        goal__user=user,
        status="done",
        completed_at__date__gte=week_start,
    ).count()

    return {
        "entries": entries_count,
        "avg_mood": avg_mood,
        "completed": completed,
    }


@login_required
def daily_briefing(request):
    stats = _daily_stats(request.user)

    try:
        briefing_text = get_daily_briefing(request.user)
        return JsonResponse(
            {
                "success": True,
                "briefing": briefing_text,
                "stats": stats,
            }
        )
    except AIConfigurationError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
                "stats": stats,
            },
            status=503,
        )
    except AIProviderError:
        return JsonResponse(
            {
                "success": False,
                "error": "The AI provider is currently unavailable. Check the configured API key, quota, or provider status.",
                "stats": stats,
            },
            status=503,
        )


@login_required
def weekly_summary(request):
    stats = _weekly_stats(request.user)

    try:
        summary_text = get_weekly_summary(request.user)
        return JsonResponse(
            {
                "success": True,
                "summary": summary_text,
                "stats": stats,
            }
        )
    except AIConfigurationError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
                "stats": stats,
            },
            status=503,
        )
    except AIProviderError:
        return JsonResponse(
            {
                "success": False,
                "error": "The AI provider is currently unavailable. Check the configured API key, quota, or provider status.",
                "stats": stats,
            },
            status=503,
        )
