from django.conf import settings
import firebase_admin
from firebase_admin import credentials


def _admin_credential_payload():
    return {
        'type': 'service_account',
        'project_id': settings.FIREBASE_PROJECT_ID,
        'private_key_id': settings.FIREBASE_PRIVATE_KEY_ID,
        'private_key': settings.FIREBASE_PRIVATE_KEY,
        'client_email': settings.FIREBASE_CLIENT_EMAIL,
        'client_id': settings.FIREBASE_CLIENT_ID,
        'auth_uri': settings.FIREBASE_AUTH_URI,
        'token_uri': settings.FIREBASE_TOKEN_URI,
        'auth_provider_x509_cert_url': settings.FIREBASE_AUTH_PROVIDER_CERT_URL,
        'client_x509_cert_url': settings.FIREBASE_CLIENT_CERT_URL,
    }


def firebase_admin_missing_settings():
    required_settings = {
        'FIREBASE_PROJECT_ID': settings.FIREBASE_PROJECT_ID,
        'FIREBASE_PRIVATE_KEY_ID': settings.FIREBASE_PRIVATE_KEY_ID,
        'FIREBASE_PRIVATE_KEY': settings.FIREBASE_PRIVATE_KEY,
        'FIREBASE_CLIENT_EMAIL': settings.FIREBASE_CLIENT_EMAIL,
        'FIREBASE_CLIENT_ID': settings.FIREBASE_CLIENT_ID,
        'FIREBASE_CLIENT_CERT_URL': settings.FIREBASE_CLIENT_CERT_URL,
    }
    return [name for name, value in required_settings.items() if not value]


def get_firebase_admin_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        missing_settings = firebase_admin_missing_settings()
        if missing_settings:
            raise RuntimeError(
                'Missing Firebase Admin settings: ' + ', '.join(missing_settings)
            )

        options = {}
        if settings.FIREBASE_STORAGE_BUCKET:
            options['storageBucket'] = settings.FIREBASE_STORAGE_BUCKET

        return firebase_admin.initialize_app(
            credentials.Certificate(_admin_credential_payload()),
            options or None,
        )
