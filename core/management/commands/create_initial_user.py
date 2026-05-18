from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates the initial user from explicit arguments or environment variables'

    def add_arguments(self, parser):
        parser.add_argument('--username')
        parser.add_argument('--password')
        parser.add_argument('--first-name', default='Jayti')
        parser.add_argument('--last-name', default='Pargal')

    def handle(self, *args, **options):
        username = options.get('username') or os.environ.get('INITIAL_USERNAME')
        password = options.get('password') or os.environ.get('INITIAL_PASSWORD')
        first_name = options.get('first_name')
        last_name = options.get('last_name')

        if not username or not password:
            raise CommandError(
                'Provide --username and --password, or set INITIAL_USERNAME and INITIAL_PASSWORD.'
            )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'first_name': first_name, 'last_name': last_name},
        )
        user.set_password(password)
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.is_active = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created user: {user.username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated password for user: {user.username}'))
