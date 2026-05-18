"""
AI-Powered Daily Morning Briefing Service
Generates personalized daily briefings using the configured production AI provider.
With caching to improve performance
"""
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from diary.models import DiaryEntry
from goals.models import Goal, Task
from astro.models import BirthChart, PlanetPosition

from core.services.ai_runtime import generate_prompt_response


class DailyBriefingService:
    """Generate personalized daily briefings for Jayti"""
    
    def __init__(self, user):
        self.user = user
        self.today = timezone.now()
        
    def get_diary_context(self):
        """Get recent diary entries and mood trends"""
        recent_entries = DiaryEntry.objects.filter(
            user=self.user,
            entry_date__gte=self.today.date() - timedelta(days=7)
        ).order_by('-entry_date')[:7]
        
        if not recent_entries:
            return None
        
        streak = 0
        for i, entry in enumerate(recent_entries):
            expected_date = self.today.date() - timedelta(days=i)
            if entry.entry_date == expected_date:
                streak += 1
            else:
                break
        
        moods = [e.mood for e in recent_entries if e.mood]
        avg_mood = sum(moods) / len(moods) if moods else None
        
        last_entry = recent_entries[0] if recent_entries else None
        last_content = last_entry.content[:200] if last_entry and last_entry.content else None
        
        return {
            'streak': streak,
            'avg_mood': avg_mood,
            'last_entry_snippet': last_content,
            'last_mood': last_entry.mood if last_entry else None,
            'entry_count': len(recent_entries),
        }
    
    def get_goals_context(self):
        """Get active goals and pending tasks"""
        active_goals = Goal.objects.filter(user=self.user, status='active')
        
        if not active_goals:
            return None
        
        pending_tasks = Task.objects.filter(
            goal__user=self.user,
            status__in=['pending', 'in_progress']
        ).order_by('due_date')[:5]
        
        overdue_tasks = Task.objects.filter(
            goal__user=self.user,
            status='pending',
            due_date__lt=self.today.date()
        ).count()
        
        today_tasks = Task.objects.filter(
            goal__user=self.user,
            status='pending',
            due_date=self.today.date()
        )
        
        return {
            'active_goals_count': active_goals.count(),
            'primary_goal': active_goals.first(),
            'pending_tasks': list(pending_tasks.values('title', 'due_date', 'department')),
            'overdue_count': overdue_tasks,
            'today_tasks': list(today_tasks.values('title', 'department')),
        }
    
    def get_astro_context(self):
        """Get today's astrological insights"""
        try:
            birth_chart = BirthChart.objects.get(user=self.user)
            return {
                'has_chart': True,
                'moon_house': PlanetPosition.objects.filter(
                    birth_chart=birth_chart,
                    planet='moon'
                ).first().house if PlanetPosition.objects.filter(
                    birth_chart=birth_chart,
                    planet='moon'
                ).exists() else None,
            }
        except BirthChart.DoesNotExist:
            return {'has_chart': False}
    
    def generate_briefing(self):
        """Generate AI-powered daily briefing"""
        diary_ctx = self.get_diary_context()
        goals_ctx = self.get_goals_context()
        astro_ctx = self.get_astro_context()
        
        context_parts = []
        
        if diary_ctx:
            context_parts.append(f"""
Diary Context:
- Writing streak: {diary_ctx['streak']} days
- Recent mood average: {diary_ctx['avg_mood']}/5
- Last entry mood: {diary_ctx['last_mood']}/5
- Last entry snippet: {diary_ctx['last_entry_snippet']}
""")
        
        if goals_ctx:
            context_parts.append(f"""
Goals Context:
- Active goals: {goals_ctx['active_goals_count']}
- Primary goal: {goals_ctx['primary_goal'].title if goals_ctx['primary_goal'] else 'None'}
- Tasks due today: {len(goals_ctx['today_tasks'])}
- Overdue tasks: {goals_ctx['overdue_count']}
- Upcoming tasks: {', '.join([t['title'] for t in goals_ctx['pending_tasks'][:3]])}
""")
        
        if astro_ctx and astro_ctx['has_chart']:
            context_parts.append(f"""
Astrological Context:
- Moon house: {astro_ctx['moon_house']}
""")
        
        context_text = '\n'.join(context_parts)
        
        prompt = f"""You are Jayti's personal AI mentor and companion. You know her deeply - her struggles, growth, goals, and journey.

Today's date: {self.today.strftime('%A, %B %d, %Y')}

Jayti's Current Context:
{context_text}

IMPORTANT INSTRUCTIONS:
1. You are NOT a generic AI assistant. You are Jayti's personal mentor who has been with her from day one.
2. Reference her specific data - diary entries, mood patterns, goals, tasks.
3. Be warm, personal, and specific. Use "you" and "your".
4. NO generic motivational quotes. Only personalized guidance based on HER data.
5. Remember her journey - acknowledge progress, patterns, and challenges.
6. Focus on actionable insights related to her goals and current tasks.
7. If she's struggling (low mood), provide specific, compassionate support.
8. Connect her astrological insights to her current life situation.
9. Keep it conversational, like a caring friend who knows her well.
10. NO EMOJIS. Use natural, warm language instead.

Generate a brief (150-200 words) morning message that:
- Greets her personally
- Acknowledges her recent progress or challenges
- Highlights today's focus based on her tasks
- Provides specific encouragement based on her mood trends
- Includes subtle astrological guidance if relevant
- Ends with a personalized reflection prompt

        Tone: Warm, supportive, personal, like a mentor who knows her journey intimately.
        Format: Plain text, 3-4 short paragraphs. NO EMOJIS.
        """

        completion = generate_prompt_response(
            prompt,
            max_tokens=300,
            temperature=0.7,
            top_p=0.9,
        )
        return completion.text


def get_daily_briefing(user):
    """Main function to get daily briefing with caching"""
    # Cache key based on user and date (briefing changes daily)
    cache_key = f"daily_briefing_{user.id}_{timezone.now().strftime('%Y%m%d')}"
    
    # Try to get from cache first
    cached_briefing = cache.get(cache_key)
    if cached_briefing:
        return cached_briefing
    
    # Generate new briefing
    service = DailyBriefingService(user)
    briefing = service.generate_briefing()
    
    # Cache for 4 hours (briefing is daily but we refresh a few times)
    cache.set(cache_key, briefing, 60 * 60 * 4)
    
    return briefing
