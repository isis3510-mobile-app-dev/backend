"""
Test-only Django settings.

Patches firebase_admin before it loads so tests can run
without a real firebase_key.json file.
"""
import os
from unittest.mock import MagicMock, patch

# Patch credentials.Certificate before backend.firebase is imported by settings.py
_cert_patcher = patch("firebase_admin.credentials.Certificate", return_value=MagicMock())
_init_patcher  = patch("firebase_admin.initialize_app")
_cert_patcher.start()
_init_patcher.start()

# Pull in all the real settings
from backend.settings import *  # noqa: F401, F403

# Only override the DB if there's no real DATABASE_URL configured.
# When DATABASE_URL is set (e.g. Postman collection runner), use real MongoDB.
if not os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
    # Silence migration noise during unit tests
    MIGRATION_MODULES = {app: None for app in INSTALLED_APPS}

