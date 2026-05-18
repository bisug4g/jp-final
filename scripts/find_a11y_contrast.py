"""Diagnose axe-core color-contrast violations across all tracked pages."""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jaytipargal.settings")
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("SECRET_KEY", "dev-find-a11y")
os.environ.setdefault("LOG_TO_FILE", "0")
os.environ.setdefault("ALLOWED_HOSTS", "*")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import django  # noqa: E402
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.core.wsgi import get_wsgi_application  # noqa: E402
from wsgiref.simple_server import make_server, WSGIRequestHandler  # noqa: E402


USERNAME = "a11y-tester"
PASSWORD = "a11y-pass-123"
PORT = 8766
BASE_URL = f"http://127.0.0.1:{PORT}"


def setup_db_and_user():
    call_command("migrate", verbosity=0, interactive=False)
    User = get_user_model()
    u, _ = User.objects.get_or_create(username=USERNAME)
    u.set_password(PASSWORD)
    u.is_active = True
    u.save()


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *a, **kw):
        pass


def start_server():
    app = get_wsgi_application()
    httpd = make_server("127.0.0.1", PORT, app, handler_class=QuietHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


AXE_CDN = "https://cdn.jsdelivr.net/npm/axe-core@4.10.0/axe.min.js"

PAGES = [
    ("dashboard", "/"),
    ("notes", "/notes/"),
    ("diary", "/diary/"),
    ("goals", "/goals/"),
    ("astro", "/astro/"),
    ("profile", "/profile/"),
]


def main():
    setup_db_and_user()
    httpd = start_server()
    time.sleep(1)

    from playwright.sync_api import sync_playwright

    out = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        page = ctx.new_page()

        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("domcontentloaded")
        page.add_script_tag(url=AXE_CDN)
        res = page.evaluate(
            "async () => await axe.run({runOnly:['color-contrast']})"
        )
        out["login"] = res.get("violations", [])

        page.fill('input[name="username"]', USERNAME)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button[type="submit"]')
        try:
            page.wait_for_url("**/dashboard/", timeout=10_000)
        except Exception:
            pass

        for label, path in PAGES:
            page.goto(f"{BASE_URL}{path}")
            page.wait_for_load_state("domcontentloaded")
            page.add_script_tag(url=AXE_CDN)
            res = page.evaluate(
                "async () => await axe.run({runOnly:['color-contrast']})"
            )
            out[label] = res.get("violations", [])

        browser.close()

    summary = {}
    for label, viols in out.items():
        nodes_info = []
        for v in viols:
            for n in v.get("nodes", []):
                any_ = n.get("any", [])
                data = {}
                for a in any_:
                    if a.get("id") == "color-contrast":
                        data = a.get("data", {}) or {}
                        break
                nodes_info.append({
                    "target": n.get("target"),
                    "html": n.get("html", "")[:250],
                    "fgColor": data.get("fgColor"),
                    "bgColor": data.get("bgColor"),
                    "contrastRatio": data.get("contrastRatio"),
                    "expectedContrastRatio": data.get("expectedContrastRatio"),
                    "fontSize": data.get("fontSize"),
                    "fontWeight": data.get("fontWeight"),
                })
        summary[label] = nodes_info

    print(json.dumps(summary, indent=2))
    httpd.shutdown()


if __name__ == "__main__":
    main()
