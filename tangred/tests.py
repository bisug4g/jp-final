from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from tangred.models import TangredProject, TangredScreen, TangredSession

User = get_user_model()


@override_settings(
    STITCH_API_KEY="test-stitch-key",
    STITCH_MCP_URL="https://stitch.googleapis.com/mcp",
    STITCH_TIMEOUT_SEC=30,
    OPENROUTER_API_KEY="test-openrouter-key",
    OPENROUTER_MODEL="nvidia/nemotron-3-super-120b-a12b:free",
    TANGRED_PRIVATE_MEDIA_BACKEND="database",
    SECURE_SSL_REDIRECT=False,
)
class TangredViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tangred-user", password="strong-pass-123")
        self.client.force_login(self.user)
        self.project = TangredProject.objects.create(
            user=self.user,
            title="Existing Tan Studio Project",
            description="Workspace for tests",
            stitch_project_id="1234567890",
        )
        self.session = TangredSession.objects.create(
            user=self.user,
            title="Founder Wardrobe",
            occasion="Investor dinner",
            body_frame="Lean athletic",
            style_goal="Look polished but not overdressed.",
        )

    def test_tangred_home_renders(self):
        response = self.client.get(reverse("tangred_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tangred")
        self.assertContains(response, "Tan Studio")

    def test_create_session_persists_local_record(self):
        upload = SimpleUploadedFile("look.jpg", b"fake-image-bytes", content_type="image/jpeg")

        response = self.client.post(
            reverse("tangred_create_session"),
            {
                "title": "Wedding Capsule",
                "occasion": "Wedding events",
                "body_frame": "Broad shoulders",
                "skin_tone": "Warm olive",
                "preferred_palette": "Chocolate, ivory",
                "style_goal": "Look elevated and sharp",
                "photos": [upload],
            },
        )

        session = TangredSession.objects.get(title="Wedding Capsule")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("tangred_session_detail", args=[session.pk]), fetch_redirect_response=False)
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.photo_count, 1)
        photo = session.photos.first()
        self.assertEqual(photo.storage_backend, "database")
        self.assertTrue(photo.storage_path)
        self.assertEqual(photo.original_name, "look.jpg")
        self.assertEqual(bytes(photo.binary_content), b"fake-image-bytes")

    def test_session_photo_endpoint_requires_owner_and_streams_image(self):
        upload = SimpleUploadedFile("look.jpg", b"fake-image-bytes", content_type="image/jpeg")
        self.client.post(
            reverse("tangred_create_session"),
            {
                "title": "Photo Access Session",
                "photos": [upload],
            },
        )
        session = TangredSession.objects.get(title="Photo Access Session")
        photo = session.photos.first()

        response = self.client.get(reverse("tangred_session_photo", args=[photo.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"fake-image-bytes")
        self.assertEqual(response["Content-Type"], "image/jpeg")

    @patch("tangred.views._create_styleboard")
    @patch("tangred.views.run_tangred_agent")
    def test_run_session_saves_agent_result(self, mock_run_tangred_agent, mock_create_styleboard):
        upload = SimpleUploadedFile("look.jpg", b"fake-image-bytes", content_type="image/jpeg")
        self.session.photos.create(image=upload)
        mock_run_tangred_agent.return_value = {
            "style_identity": "Quiet Power Tailoring",
            "body_summary": "Balanced frame with clean vertical lines.",
            "outfit_direction": "Use softened structure and rich neutrals.",
            "wardrobe_blueprint": ["Single-breasted jacket", "Straight trousers"],
            "accessory_focus": "Dark brown leather belt and clean derby shoes.",
            "color_story": "Lean into espresso, charcoal and ivory.",
            "confidence_notes": "Keep trouser break minimal and grooming crisp.",
            "visualization_prompt": "Premium mobile styleboard with founder wardrobe guidance.",
            "provider": "openrouter",
            "model": "nvidia/nemotron-3-super-120b-a12b:free",
            "raw_response": {"ok": True},
        }
        mock_create_styleboard.return_value = (None, None)

        response = self.client.post(reverse("tangred_run_session", args=[self.session.pk]))

        self.session.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("tangred_session_detail", args=[self.session.pk]), fetch_redirect_response=False)
        self.assertEqual(self.session.status, "READY")
        self.assertEqual(self.session.style_identity, "Quiet Power Tailoring")
        self.assertEqual(self.session.openrouter_provider, "openrouter")
        self.assertEqual(self.session.openrouter_model, "nvidia/nemotron-3-super-120b-a12b:free")

    @patch("tangred.views.list_projects")
    def test_tan_studio_home_renders(self, mock_list_projects):
        mock_list_projects.return_value = []

        response = self.client.get(reverse("tan_studio_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tan Studio")

    @patch("tangred.views.optimize_tan_studio_prompt")
    @patch("tangred.views.generate_screen_from_text")
    def test_generate_screen_creates_local_screen_record(self, mock_generate_screen, mock_optimize_prompt):
        mock_optimize_prompt.return_value = {
            "prompt": "Optimized Tan Studio brief",
            "provider": "openrouter",
            "model": "nvidia/nemotron-3-super-120b-a12b:free",
        }
        mock_generate_screen.return_value = {
            "projectId": self.project.stitch_project_id,
            "sessionId": "session-42",
            "outputComponents": [
                {"text": "Premium mobile login screen"},
                {
                    "design": {
                        "screens": [
                            {
                                "name": "projects/1234567890/screens/2222",
                                "title": "Login Screen",
                                "screenshot": {"downloadUrl": "https://example.com/screen.png"},
                                "htmlCode": {"downloadUrl": "https://example.com/screen.html"},
                                "screenMetadata": {"status": "COMPLETE"},
                            }
                        ]
                    }
                },
            ],
        }

        response = self.client.post(
            reverse("tan_studio_generate_screen", args=[self.project.pk]),
            {
                "prompt": "Build a warm mobile login screen",
                "device_type": "MOBILE",
                "model_id": "GEMINI_3_FLASH",
            },
        )

        screen = TangredScreen.objects.get(project=self.project)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("tan_studio_screen_detail", args=[screen.pk]), fetch_redirect_response=False)
        self.assertEqual(screen.title, "Login Screen")
        self.assertEqual(screen.optimized_prompt, "Optimized Tan Studio brief")

    @patch("tangred.views.get_screen")
    def test_refresh_screen_updates_existing_assets(self, mock_get_screen):
        screen = TangredScreen.objects.create(
            project=self.project,
            title="Login Screen",
            prompt="Build a login screen",
            stitch_screen_name="projects/1234567890/screens/2222",
            stitch_screen_id="2222",
            status="PENDING",
        )
        mock_get_screen.return_value = {
            "title": "Login Screen Updated",
            "screenshot": {"downloadUrl": "https://example.com/refreshed.png"},
            "htmlCode": {"downloadUrl": "https://example.com/refreshed.html"},
            "screenMetadata": {"status": "COMPLETE"},
        }

        response = self.client.post(reverse("tan_studio_refresh_screen", args=[screen.pk]))

        screen.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("tan_studio_screen_detail", args=[screen.pk]), fetch_redirect_response=False)
        self.assertEqual(screen.title, "Login Screen Updated")
        self.assertEqual(screen.status, "COMPLETE")
