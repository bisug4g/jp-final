"""
AI Weekly Summary Service
Generates personalized weekly summaries using the configured production AI provider.
With caching for performance
"""
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from diary.models import DiaryEntry
from goals.models import Task
from notes.models import Note

from core.services.ai_runtime import generate_prompt_response


class WeeklySummaryService:
    """Generate AI-powered weekly summaries"""
    
    def __init__(self, user):
        self.user = user
        self.today = timezone.now()
        self.week_start = self.today - timedelta(days=self.today.weekday())
        self.week_end = self.week_start + timedelta(days=6)
    
    def get_week_context(self):
        """Gather all data from the past week"""
        # Diary entries
        diary_entries = DiaryEntry.objects.filter(
            user=self.user,
            entry_date__gte=self.week_start.date(),
            entry_date__lte=self.week_end.date()
        )
        
        diary_count = diary_entries.count()
        moods = [e.mood for e in diary_entries if e.mood]
        avg_mood = sum(moods) / len(moods) if moods else None
        
        # Tasks completed
        completed_tasks = Task.objects.filter(
            goal__user=self.user,
            status='done',
            completed_at__gte=self.week_start,
            completed_at__lte=self.week_end
        )
        
        # Notes created
        notes_created = Note.objects.filter(
            user=self.user,
            created_at__gte=self.week_start,
            created_at__lte=self.week_end
        ).count()
        
        return {
            'diary_count': diary_count,
            'avg_mood': avg_mood,
            'completed_tasks': list(completed_tasks.values('title', 'department')),
            'notes_created': notes_created,
            'week_start': self.week_start.strftime('%B %d'),
            'week_end': self.week_end.strftime('%B %d, %Y'),
        }
    
    def generate_summary(self):
        """Generate AI-powered weekly summary"""
        context = self.get_week_context()
        
        prompt = f"""You are Jayti's personal AI mentor who knows her journey from day one. Generate a personalized weekly summary.

Week: {context['week_start']} - {context['week_end']}

Jayti's Activity:
- Diary entries: {context['diary_count']}
- Average mood: {context['avg_mood']}/5
- Tasks completed: {len(context['completed_tasks'])}
- Notes created: {context['notes_created']}

Completed tasks:
{chr(10).join([f"- {t['title']} ({t['department']})" for t in context['completed_tasks'][:5]])}

INSTRUCTIONS:
1. You are her MENTOR, not a generic AI. Reference her specific journey and data.
2. Celebrate specific accomplishments, not generic praise.
3. Acknowledge patterns in her behavior and progress.
4. Connect mood to activities and provide insights.
5. If struggling, provide compassionate, specific support.
6. Give actionable insights for next week based on this week.
7. NO EMOJIS. Use warm, natural language.
        8. Be personal and specific to HER data.

        Generate 200-250 words with 4-5 paragraphs. NO EMOJIS.
        """

        completion = generate_prompt_response(
            prompt,
            max_tokens=400,
            temperature=0.7,
            top_p=0.9,
        )
        return completion.text


def get_weekly_summary(user):
    """Main function to get weekly summary with caching"""
    # Cache weekly summary for 6 hours
    cache_key = f"weekly_summary_{user.id}_{timezone.now().strftime('%Y%W')}"
    
    cached_summary = cache.get(cache_key)
    if cached_summary:
        return cached_summary
    
    service = WeeklySummaryService(user)
    summary = service.generate_summary()
    
    cache.set(cache_key, summary, 60 * 60 * 6)
    return summary
