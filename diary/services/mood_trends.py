"""
Mood Trend Analysis Service
"""
from django.utils import timezone
from datetime import timedelta
from diary.models import DiaryEntry
from collections import defaultdict
import json


class MoodTrendService:
    """Analyze mood trends over time"""
    
    def __init__(self, user):
        self.user = user
    
    def get_mood_data(self, days=30):
        """Get mood data for the last N days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        entries = DiaryEntry.objects.filter(
            user=self.user,
            entry_date__gte=start_date,
            entry_date__lte=end_date,
            mood__isnull=False
        ).order_by('entry_date')
        
        mood_data = []
        for entry in entries:
            mood_data.append({
                'date': entry.entry_date.strftime('%Y-%m-%d'),
                'mood': entry.mood,
                'mood_note': entry.mood_note,
            })
        
        return mood_data
    
    def get_weekly_averages(self, weeks=12):
        """Get weekly mood averages"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(weeks=weeks)
        
        entries = DiaryEntry.objects.filter(
            user=self.user,
            entry_date__gte=start_date,
            mood__isnull=False
        ).order_by('entry_date')
        
        weekly_data = defaultdict(list)
        
        for entry in entries:
            week_start = entry.entry_date - timedelta(days=entry.entry_date.weekday())
            weekly_data[week_start].append(entry.mood)
        
        result = []
        for week_start in sorted(weekly_data.keys()):
            moods = weekly_data[week_start]
            result.append({
                'week': week_start.strftime('%Y-%m-%d'),
                'avg_mood': round(sum(moods) / len(moods), 2),
                'entry_count': len(moods),
            })
        
        return result
    
    def get_mood_distribution(self, days=90):
        """Get mood distribution (how many days at each mood level)"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        entries = DiaryEntry.objects.filter(
            user=self.user,
            entry_date__gte=start_date,
            mood__isnull=False
        )
        
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for entry in entries:
            distribution[entry.mood] += 1
        
        return distribution
    
    def get_insights(self):
        """Generate mood insights"""
        recent_moods = self.get_mood_data(days=30)
        
        if not recent_moods:
            return {
                'has_data': False,
                'message': 'Start tracking your mood to see insights!'
            }
        
        moods = [m['mood'] for m in recent_moods]
        avg_mood = sum(moods) / len(moods)
        
        # Trend detection
        if len(moods) >= 7:
            recent_avg = sum(moods[-7:]) / 7
            older_avg = sum(moods[:-7]) / len(moods[:-7]) if len(moods) > 7 else avg_mood
            
            if recent_avg > older_avg + 0.5:
                trend = 'improving'
            elif recent_avg < older_avg - 0.5:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'has_data': True,
            'avg_mood': round(avg_mood, 2),
            'trend': trend,
            'entry_count': len(recent_moods),
            'best_mood': max(moods),
            'lowest_mood': min(moods),
        }


def get_mood_chart_data(user, period='month'):
    """Get mood data formatted for Chart.js"""
    service = MoodTrendService(user)
    
    if period == 'month':
        data = service.get_mood_data(days=30)
        return {
            'labels': [d['date'] for d in data],
            'data': [d['mood'] for d in data],
        }
    elif period == 'week':
        data = service.get_weekly_averages(weeks=12)
        return {
            'labels': [d['week'] for d in data],
            'data': [d['avg_mood'] for d in data],
        }
    
    return {'labels': [], 'data': []}
