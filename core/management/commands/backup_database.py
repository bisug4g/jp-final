from django.core.management.base import BaseCommand
from django.core import serializers
from django.contrib.auth.models import User
from notes.models import Note, Tag, NoteFolder
from diary.models import DiaryEntry
from goals.models import Goal, Task
import json
from datetime import datetime
import os

class Command(BaseCommand):
    help = 'Backup database to JSON file'

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = 'backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = f'{backup_dir}/jayti_backup_{timestamp}.json'
        
        data = {
            'users': json.loads(serializers.serialize('json', User.objects.all())),
            'notes': json.loads(serializers.serialize('json', Note.objects.all())),
            'tags': json.loads(serializers.serialize('json', Tag.objects.all())),
            'folders': json.loads(serializers.serialize('json', NoteFolder.objects.all())),
            'diary': json.loads(serializers.serialize('json', DiaryEntry.objects.all())),
            'goals': json.loads(serializers.serialize('json', Goal.objects.all())),
            'tasks': json.loads(serializers.serialize('json', Task.objects.all())),
            'timestamp': timestamp
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Backup created: {filename}'))
