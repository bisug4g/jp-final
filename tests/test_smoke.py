"""
Smoke tests that run without any external services.
Uses Django's in-process test client so CI doesn't need a live server.
"""
import json

from django.test import Client, TestCase


class HealthCheckTests(TestCase):
    def test_health_endpoint_returns_healthy(self):
        response = Client().get('/health')
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload['status'], 'healthy')
        self.assertIn('timestamp', payload)

    def test_health_endpoint_with_trailing_slash(self):
        response = Client().get('/health/')
        self.assertEqual(response.status_code, 200)


class RobotsTxtTests(TestCase):
    def test_robots_txt_served(self):
        response = Client().get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('text/plain'))


class ApiCatchAllTests(TestCase):
    def test_api_prefix_returns_404_json(self):
        response = Client().get('/api/')
        self.assertEqual(response.status_code, 404)
        payload = json.loads(response.content)
        self.assertEqual(payload['error'], 'API endpoint not found')
