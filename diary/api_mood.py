from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from diary.models import DiaryEntry

@login_required
def mood_trends(request):
    period = request.GET.get('period', 'month')
    
    if period == 'week':
        days = 7
    elif period == 'month':
        days = 30
    else:
        days = 90
    
    start_date = datetime.now().date() - timedelta(days=days)
    
    entries = DiaryEntry.objects.filter(
        user=request.user,
        entry_date__gte=start_date,
        mood__isnull=False
    ).order_by('entry_date')
    
    labels = []
    data = []
    
    for entry in entries:
        labels.append(entry.entry_date.strftime('%b %d'))
        data.append(entry.mood)
    
    return JsonResponse({
        'success': True,
        'chart_data': {
            'labels': labels,
            'data': data
        },
        'stats': {
            'avg_mood': sum(data) / len(data) if data else 0,
            'entries': len(data)
        }
    })
