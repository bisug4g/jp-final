import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


class AIChatAvailabilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='chat-user', password='strong-pass-123')
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
    def test_send_message_returns_503_without_provider(self):
        response = self.client.post(
            reverse('ai_send_message'),
            data=json.dumps({'message': 'hello'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn('error', response.json())

    def test_send_message_requires_login(self):
        self.client.logout()

        response = self.client.post(
            reverse('ai_send_message'),
            data=json.dumps({'message': 'hello'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 302)
