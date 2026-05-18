from django.conf import settings
from django.core.management.base import BaseCommand

from core.services.firebase_admin import firebase_admin_missing_settings, get_firebase_admin_app


class Command(BaseCommand):
    help = 'Debug Firebase configuration for a Railway-hosted deployment'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(self.style.MIGRATE_HEADING('FIREBASE CONFIG DEBUGGER'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))

        public_config = {
            'FIREBASE_API_KEY': settings.FIREBASE_API_KEY,
            'FIREBASE_AUTH_DOMAIN': settings.FIREBASE_AUTH_DOMAIN,
            'FIREBASE_PROJECT_ID': settings.FIREBASE_PROJECT_ID,
            'FIREBASE_STORAGE_BUCKET': settings.FIREBASE_STORAGE_BUCKET,
            'FIREBASE_MESSAGING_SENDER_ID': settings.FIREBASE_MESSAGING_SENDER_ID,
            'FIREBASE_APP_ID': settings.FIREBASE_APP_ID,
            'FIREBASE_MEASUREMENT_ID': settings.FIREBASE_MEASUREMENT_ID,
        }

        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('1. Public web config'))
        for name, value in public_config.items():
            if value:
                self.stdout.write(self.style.SUCCESS(f'   ✓ {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠ {name}: not set'))

        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('2. Firebase Admin config'))
        missing_settings = firebase_admin_missing_settings()
        if missing_settings:
            self.stdout.write(
                self.style.WARNING(
                    '   ⚠ Admin SDK not ready: missing ' + ', '.join(missing_settings)
                )
            )
        else:
            try:
                app = get_firebase_admin_app()
                self.stdout.write(self.style.SUCCESS(f'   ✓ Admin SDK initialized: {app.name}'))
            except RuntimeError as error:
                self.stdout.write(self.style.ERROR(f'   ✗ Admin SDK configuration error: {error}'))
            except ValueError as error:
                self.stdout.write(self.style.ERROR(f'   ✗ Admin SDK initialization failed: {error}'))

        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('3. Deployment shape'))
        self.stdout.write('   • Keep Django backend on Railway')
        self.stdout.write('   • Use Firebase for client services like Analytics')
        self.stdout.write('   • Keep existing VAPID web-push flow unchanged')

        self.stdout.write('\n')
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
