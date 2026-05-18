"""
Enhanced API Views for New Features
Add these to core/views.py or create core/api_views.py
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
import json

# Import services
from core.services.ai_runtime import AIConfigurationError, AIProviderError
from core.services.daily_briefing import get_daily_briefing
from core.services.weekly_summary import get_weekly_summary
from core.services.activity_tracker import get_activity_calendar, get_activity_stats, record_login
from diary.services.mood_trends import get_mood_chart_data, MoodTrendService
from diary.services.search import search_diary
from diary.services.pdf_export import export_diary_pdf
from goals.services.progress_analytics import get_progress_chart_data
from astro.services.daily_insight import get_daily_astro_insight
from core.models import PushSubscription, NotificationSchedule


@login_required
@require_http_methods(["GET"])
def api_daily_briefing(request):
    """Get AI-powered daily briefing"""
    try:
        briefing = get_daily_briefing(request.user)
        return JsonResponse({
            'success': True,
            'briefing': briefing,
        })
    except (AIConfigurationError, AIProviderError) as exc:
        return JsonResponse({
            'success': False,
            'error': str(exc),
        }, status=503)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_weekly_summary(request):
    """Get AI-powered weekly summary"""
    try:
        summary = get_weekly_summary(request.user)
        return JsonResponse({
            'success': True,
            'summary': summary,
        })
    except (AIConfigurationError, AIProviderError) as exc:
        return JsonResponse({
            'success': False,
            'error': str(exc),
        }, status=503)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_mood_trends(request):
    """Get mood trend data for charts"""
    try:
        period = request.GET.get('period', 'month')
        chart_data = get_mood_chart_data(request.user, period)
        
        service = MoodTrendService(request.user)
        insights = service.get_insights()
        distribution = service.get_mood_distribution()
        
        return JsonResponse({
            'success': True,
            'chart_data': chart_data,
            'insights': insights,
            'distribution': distribution,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_goal_progress(request):
    """Get goal progress data for charts"""
    try:
        chart_data = get_progress_chart_data(request.user)
        return JsonResponse({
            'success': True,
            'charts': chart_data,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_daily_astro(request):
    """Get daily astrological insight"""
    try:
        insight = get_daily_astro_insight(request.user)
        return JsonResponse({
            'success': True,
            'insight': insight,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_diary_search(request):
    """Search diary entries"""
    try:
        query = request.GET.get('q', '')
        mood = request.GET.get('mood')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        filters = {}
        if mood:
            try:
                filters['mood'] = int(mood)
            except (ValueError, TypeError):
                pass
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        results = search_diary(request.user, query, filters)
        
        entries = []
        for entry in results[:50]:  # Limit to 50 results
            entries.append({
                'id': str(entry.id),
                'date': entry.entry_date.strftime('%Y-%m-%d'),
                'content_preview': entry.content[:200] if entry.content else '',
                'mood': entry.mood,
                'mood_note': entry.mood_note,
            })
        
        return JsonResponse({
            'success': True,
            'results': entries,
            'count': len(entries),
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_export_diary_pdf(request):
    """Export diary entries to PDF"""
    try:
        from django.http import HttpResponse
        from datetime import datetime
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        pdf_buffer = export_diary_pdf(request.user, start_date, end_date)
        
        if pdf_buffer:
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="diary_export_{datetime.now().strftime("%Y%m%d")}.pdf"'
            return response
        else:
            return JsonResponse({
                'success': False,
                'error': 'No entries found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def api_push_subscribe(request):
    """Subscribe to push notifications"""
    try:
        data = json.loads(request.body)
        
        subscription, created = PushSubscription.objects.update_or_create(
            user=request.user,
            endpoint=data['endpoint'],
            defaults={
                'p256dh': data['keys']['p256dh'],
                'auth': data['keys']['auth'],
                'is_active': True,
            }
        )
        
        # Create notification schedule if doesn't exist
        NotificationSchedule.objects.get_or_create(
            user=request.user,
            defaults={'enabled': True}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Subscribed to notifications'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def api_push_unsubscribe(request):
    """Unsubscribe from push notifications"""
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        
        if endpoint:
            PushSubscription.objects.filter(
                user=request.user,
                endpoint=endpoint
            ).update(is_active=False)
        else:
            PushSubscription.objects.filter(
                user=request.user
            ).update(is_active=False)
        
        return JsonResponse({
            'success': True,
            'message': 'Unsubscribed from notifications'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def api_notification_settings(request):
    """Get or update notification settings"""
    try:
        schedule, created = NotificationSchedule.objects.get_or_create(
            user=request.user
        )
        
        if request.method == 'POST':
            data = json.loads(request.body)
            
            if 'enabled' in data:
                schedule.enabled = data['enabled']
            if 'morning_time' in data:
                schedule.morning_time = data['morning_time']
            if 'evening_reminder' in data:
                schedule.evening_reminder = data['evening_reminder']
            if 'evening_time' in data:
                schedule.evening_time = data['evening_time']
            
            schedule.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Settings updated'
            })
        else:
            return JsonResponse({
                'success': True,
                'settings': {
                    'enabled': schedule.enabled,
                    'morning_time': schedule.morning_time.strftime('%H:%M'),
                    'evening_reminder': schedule.evening_reminder,
                    'evening_time': schedule.evening_time.strftime('%H:%M'),
                    'timezone': schedule.timezone,
                }
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_activity_calendar(request):
    """Get activity calendar data from Feb 6, 2026 onwards"""
    try:
        calendar_data = get_activity_calendar(request.user)
        stats = get_activity_stats(request.user)
        
        return JsonResponse({
            'success': True,
            'calendar': calendar_data,
            'stats': stats
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_activity_stats(request):
    """Get activity statistics summary"""
    try:
        stats = get_activity_stats(request.user)
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
