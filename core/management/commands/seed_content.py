from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notes.models import Note, Tag
from diary.models import DiaryEntry
from datetime import datetime

class Command(BaseCommand):
    help = 'Seed welcome content for new users'

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username='jayati')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User jayati not found'))
            return
        
        # Create welcome note
        if not Note.objects.filter(user=user, title__contains='Welcome').exists():
            welcome_note = Note.objects.create(
                user=user,
                title='Welcome to Your Personal Space',
                content='''<p>Dear Jayti,</p>

<p>This is your personal sanctuary - a space designed just for you to reflect, plan, and grow.</p>

<h3>What You Can Do Here:</h3>
<ul>
<li><strong>Notes:</strong> Capture thoughts, ideas, and reminders</li>
<li><strong>Diary:</strong> Record your daily experiences and emotions</li>
<li><strong>Goals:</strong> Set and track your personal and professional objectives</li>
<li><strong>Astro:</strong> Explore your Vedic birth chart and daily insights</li>
<li><strong>AI Chat:</strong> Get personalized guidance and support</li>
</ul>

<p>Everything here is private and secure. This is your space to be authentic.</p>

<p>With care,<br>Vivek</p>''',
                is_pinned=True
            )
            self.stdout.write(self.style.SUCCESS('✅ Welcome note created'))
        
        # Create sample diary entry
        today = datetime.now().date()
        if not DiaryEntry.objects.filter(user=user, entry_date=today).exists():
            DiaryEntry.objects.create(
                user=user,
                entry_date=today,
                content='Today marks the beginning of my journey with this personal companion. I\'m looking forward to using this space for reflection and growth.',
                mood=4,
                mood_note='Hopeful and optimistic'
            )
            self.stdout.write(self.style.SUCCESS('✅ Sample diary entry created'))
        
        # Create tags
        tags = ['Personal', 'Work', 'Ideas', 'Important']
        for tag_name in tags:
            Tag.objects.get_or_create(name=tag_name)
        
        self.stdout.write(self.style.SUCCESS('✅ Seed content complete'))
