from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from core.services.ai_runtime import available_providers

User = get_user_model()


class AIEndpointAvailabilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='strong-pass-123')
        self.client.force_login(self.user)

    @override_settings(
        EMERGENT_API_KEY='',
        GITHUB_MODELS_TOKEN='',
        GEMINI_API_KEY='',
        FIREBASE_PROJECT_ID='',
        FIREBASE_PRIVATE_KEY_ID='',
        FIREBASE_PRIVATE_KEY='',
        FIREBASE_CLIENT_EMAIL='',
        FIREBASE_CLIENT_ID='',
        FIREBASE_CLIENT_CERT_URL='',
    )
    def test_daily_briefing_requires_configured_provider(self):
        response = self.client.get(reverse('api_daily_briefing'))

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()['success'])

    @override_settings(
        EMERGENT_API_KEY='',
        GITHUB_MODELS_TOKEN='',
        GEMINI_API_KEY='',
        FIREBASE_PROJECT_ID='',
        FIREBASE_PRIVATE_KEY_ID='',
        FIREBASE_PRIVATE_KEY='',
        FIREBASE_CLIENT_EMAIL='',
        FIREBASE_CLIENT_ID='',
        FIREBASE_CLIENT_CERT_URL='',
    )
    def test_weekly_summary_requires_configured_provider(self):
        response = self.client.get(reverse('api_weekly_summary'))

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()['success'])


class CreateInitialUserCommandTests(TestCase):
    def test_create_initial_user_requires_explicit_credentials(self):
        with self.assertRaises(CommandError):
            call_command('create_initial_user', stdout=StringIO())


class AIProviderDetectionTests(TestCase):
    @override_settings(
        EMERGENT_API_KEY='',
        GITHUB_MODELS_TOKEN='ghp_test_token',
        GEMINI_API_KEY='',
        FIREBASE_PROJECT_ID='',
        FIREBASE_PRIVATE_KEY_ID='',
        FIREBASE_PRIVATE_KEY='',
        FIREBASE_CLIENT_EMAIL='',
        FIREBASE_CLIENT_ID='',
        FIREBASE_CLIENT_CERT_URL='',
    )
    def test_github_models_provider_detected_from_token(self):
        self.assertIn('github-models', available_providers())

    @override_settings(
        EMERGENT_API_KEY='',
        GEMINI_API_KEY='',
        FIREBASE_PROJECT_ID='jayti-c7605',
        FIREBASE_PRIVATE_KEY_ID='key-id',
        FIREBASE_PRIVATE_KEY='-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n',
        FIREBASE_CLIENT_EMAIL='firebase-adminsdk@example.iam.gserviceaccount.com',
        FIREBASE_CLIENT_ID='123456',
        FIREBASE_CLIENT_CERT_URL='https://example.com/cert',
    )
    def test_vertex_provider_detected_from_firebase_credentials(self):
        self.assertIn('vertex', available_providers())
