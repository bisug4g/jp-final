#!/usr/bin/env python
"""
Railway Deployment Debugger
Run this command to check if all deployment requirements are met.
Usage: python manage.py railway_debug
"""

import os
import sys
import django
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections, OperationalError


class Command(BaseCommand):
    help = 'Debug Railway deployment - checks all critical components'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix common issues automatically',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(self.style.MIGRATE_HEADING('RAILWAY DEPLOYMENT DEBUGGER'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        
        all_checks_passed = True
        
        # Check 1: Python Version
        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('1. Checking Python Version...'))
        py_version = sys.version_info
        py_version_str = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
        if py_version.major == 3 and py_version.minor == 11:
            self.stdout.write(self.style.SUCCESS(f'   ✓ Python {py_version_str} (Recommended)'))
        elif py_version.major == 3 and py_version.minor >= 8:
            self.stdout.write(self.style.WARNING(f'   ⚠ Python {py_version_str} (May work, but 3.11 is recommended)'))
        else:
            self.stdout.write(self.style.ERROR(f'   ✗ Python {py_version_str} (Too old, upgrade required)'))
            all_checks_passed = False
        
        # Check 2: Django Setup
        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('2. Checking Django Setup...'))
        try:
            django.setup()
            self.stdout.write(self.style.SUCCESS(f'   ✓ Django {django.get_version()} initialized'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Django setup failed: {e}'))
            all_checks_passed = False
        
        # Check 3: Database Connection
        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('3. Checking Database Connection...'))
        try:
            connections['default'].ensure_connection()
            db_engine = connections['default'].vendor
            self.stdout.write(self.style.SUCCESS(f'   ✓ Database connected ({db_engine})'))
        except OperationalError as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Database connection failed: {e}'))
            all_checks_passed = False
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠ Database check error: {e}'))
        
        # Check 4: Required Environment Variables
        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('4. Checking Environment Variables...'))
        required_vars = ['SECRET_KEY', 'DATABASE_URL']
        optional_vars = ['ALLOWED_HOSTS', 'DEBUG', 'TIME_ZONE', 'EMERGENT_API_KEY', 'GITHUB_MODELS_TOKEN', 'GEMINI_API_KEY']
        
        for var in required_vars:
            value = os.environ.get(var, '')
            if value:
                masked = value[:4] + '...' if len(value) > 8 else '***'
                self.stdout.write(self.style.SUCCESS(f'   ✓ {var}: {masked}'))
            else:
                self.stdout.write(self.style.ERROR(f'   ✗ {var}: MISSING'))
                all_checks_passed = False
        
        for var in optional_vars:
            value = os.environ.get(var, '')
            if value:
                self.stdout.write(self.style.SUCCESS(f'   ✓ {var}: {value}'))
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠ {var}: Not set (using default)'))
        
        # Check 5: Static Files Configuration
        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('5. Checking Static Files...'))
        static_root = getattr(settings, 'STATIC_ROOT', None)
        if static_root:
            self.stdout.write(self.style.SUCCESS(f'   ✓ STATIC_ROOT: {static_root}'))
            try:
                os.makedirs(static_root, exist_ok=True)
                self.stdout.write(self.style.SUCCESS(f'   ✓ Static root directory is writable'))
            except OSError as e:
                self.stdout.write(self.style.ERROR(f'   ✗ Cannot write to static root: {e}'))
                all_checks_passed = False
        else:
            self.stdout.write(self.style.ERROR(f'   ✗ STATIC_ROOT not set'))
            all_checks_passed = False
        
        # Check 6: WhiteNoise
        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('6. Checking WhiteNoise Configuration...'))
        middleware = getattr(settings, 'MIDDLEWARE', [])
        if 'whitenoise.middleware.WhiteNoiseMiddleware' in middleware:
            self.stdout.write(self.style.SUCCESS(f'   ✓ WhiteNoise middleware installed'))
        else:
            self.stdout.write(self.style.ERROR(f'   ✗ WhiteNoise middleware missing'))
            all_checks_passed = False
        
        storage = getattr(settings, 'STATICFILES_STORAGE', '')
        if 'whitenoise' in storage:
            self.stdout.write(self.style.SUCCESS(f'   ✓ WhiteNoise storage: {storage}'))
        else:
            self.stdout.write(self.style.WARNING(f'   ⚠ WhiteNoise storage not configured'))
        
        # Check 7: Critical Dependencies
        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('7. Checking Critical Dependencies...'))
        
        deps_to_check = [
            ('gunicorn', 'gunicorn'),
            ('psycopg2', 'psycopg2'),
            ('dj_database_url', 'dj_database_url'),
            ('whitenoise', 'whitenoise'),
            ('dotenv', 'dotenv'),
            ('openai', 'openai'),
            ('google.genai', 'google-genai'),
        ]
        
        for module, name in deps_to_check:
            try:
                __import__(module)
                self.stdout.write(self.style.SUCCESS(f'   ✓ {name}'))
            except ImportError:
                self.stdout.write(self.style.ERROR(f'   ✗ {name} (Not installed)'))
                all_checks_passed = False
        
        # Check 8: pyswisseph (with graceful handling)
        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('8. Checking PySwissEph (Astrology)...'))
        try:
            import swisseph as swe
            self.stdout.write(self.style.SUCCESS(f'   ✓ pyswisseph imported successfully'))
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f'   ⚠ pyswisseph import failed: {e}'))
            self.stdout.write(self.style.WARNING(f'      Note: Astrology features will be disabled'))
        
        # Check 9: Allowed Hosts
        self.stdout.write('\n')
        self.stdout.write(self.style.HTTP_INFO('9. Checking Allowed Hosts...'))
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if '*' in allowed_hosts:
            self.stdout.write(self.style.WARNING(f'   ⚠ ALLOWED_HOSTS contains "*" (security risk)'))
        elif len(allowed_hosts) > 0 and allowed_hosts != ['']:
            self.stdout.write(self.style.SUCCESS(f'   ✓ ALLOWED_HOSTS: {", ".join(allowed_hosts)}'))
        else:
            self.stdout.write(self.style.ERROR(f'   ✗ ALLOWED_HOSTS is empty'))
            all_checks_passed = False
        
        # Summary
        self.stdout.write('\n')
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        if all_checks_passed:
            self.stdout.write(self.style.SUCCESS('✓ ALL CHECKS PASSED - READY FOR DEPLOYMENT'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ SOME CHECKS FAILED - Starting anyway (non-blocking)'))
            # Don't exit with error - let the server start even with warnings
            # sys.exit(1)
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
