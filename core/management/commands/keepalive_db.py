"""
Management command: keepalive_db
=================================
Pings the database with a lightweight query to prevent Supabase (or any
free-tier PostgreSQL provider) from suspending the project after inactivity.

Typical usage — add a Railway cron job that runs every 5–6 days:

    python manage.py keepalive_db

Or combine with a Railway Cron Service:
    Schedule: 0 12 */5 * *   (noon every 5 days)
    Command:  python manage.py keepalive_db
"""

from django.core.management.base import BaseCommand
from django.db import connection, OperationalError
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Ping the database to prevent free-tier suspension (Supabase keep-alive)"

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            if result and result[0] == 1:
                self.stdout.write(self.style.SUCCESS("✅ Database ping successful — connection is alive."))
                logger.info("keepalive_db: database ping OK")
            else:
                self.stdout.write(self.style.WARNING("⚠️  Unexpected response from database ping."))
                logger.warning("keepalive_db: unexpected ping response: %s", result)

        except OperationalError as exc:
            self.stderr.write(self.style.ERROR(f"❌ Database ping failed: {exc}"))
            logger.error("keepalive_db: OperationalError during ping: %s", exc)
            raise SystemExit(1)
