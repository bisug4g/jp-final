# Generated migration for notification models
# Run: python manage.py makemigrations core
# Then: python manage.py migrate

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PushSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.URLField(max_length=500, unique=True)),
                ('p256dh', models.CharField(max_length=200)),
                ('auth', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='push_subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'endpoint')},
            },
        ),
        migrations.CreateModel(
            name='NotificationSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True)),
                ('morning_time', models.TimeField(default='09:00')),
                ('evening_reminder', models.BooleanField(default=True)),
                ('evening_time', models.TimeField(default='20:00')),
                ('timezone', models.CharField(default='Asia/Kolkata', max_length=50)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_schedule', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
