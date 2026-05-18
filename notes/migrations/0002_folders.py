# Generated migration for note folders
# Run: python manage.py makemigrations notes
# Then: python manage.py migrate

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NoteFolder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('color', models.CharField(default='#E3F2FD', max_length=7)),
                ('icon', models.CharField(default='📁', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subfolders', to='notes.notefolder')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='note_folders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('user', 'name', 'parent')},
            },
        ),
        migrations.AddField(
            model_name='note',
            name='folder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notes', to='notes.notefolder'),
        ),
    ]
