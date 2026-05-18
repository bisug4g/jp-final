#!/usr/bin/env python3
"""
generate_vapid_keys.py
======================
Run this once to generate VAPID keys for Web Push Notifications.

Usage:
    python scripts/generate_vapid_keys.py

Then copy the output into your Railway / .env secrets:
    VAPID_PRIVATE_KEY=<private key>
    VAPID_PUBLIC_KEY=<public key>
    VAPID_ADMIN_EMAIL=admin@jaytibirthday.in
"""

try:
    from py_vapid import Vapid
except ImportError:
    print("Installing py_vapid...")
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "py_vapid"])
    from py_vapid import Vapid

import base64

vapid = Vapid()
vapid.generate_keys()

private_key = base64.urlsafe_b64encode(
    vapid.private_key.private_bytes(
        encoding=__import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding']).Encoding.Raw,
        format=__import__('cryptography.hazmat.primitives.serialization', fromlist=['PrivateFormat']).PrivateFormat.Raw,
        encryption_algorithm=__import__('cryptography.hazmat.primitives.serialization', fromlist=['NoEncryption']).NoEncryption(),
    )
).rstrip(b'=').decode()

public_key = base64.urlsafe_b64encode(
    vapid.public_key.public_bytes(
        encoding=__import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding']).Encoding.X962,
        format=__import__('cryptography.hazmat.primitives.serialization', fromlist=['PublicFormat']).PublicFormat.UncompressedPoint,
    )
).rstrip(b'=').decode()

print("\n✅ VAPID Keys Generated — add these to your Railway environment variables:\n")
print(f"VAPID_PRIVATE_KEY={private_key}")
print(f"VAPID_PUBLIC_KEY={public_key}")
print(f"VAPID_ADMIN_EMAIL=admin@jaytibirthday.in")
print("\nKeep VAPID_PRIVATE_KEY secret. VAPID_PUBLIC_KEY is safe to expose in frontend JS.")
