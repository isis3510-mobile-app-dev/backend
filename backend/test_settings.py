"""
Test-only Django settings.

Patches firebase_admin before it loads so tests can run
without a real firebase_key.json file.
"""
from unittest.mock import MagicMock, patch

# Patch credentials.Certificate before backend.firebase is imported by settings.py
_cert_patcher = patch("firebase_admin.credentials.Certificate", return_value=MagicMock())
_init_patcher  = patch("firebase_admin.initialize_app")
_cert_patcher.start()
_init_patcher.start()

# Pull in all the real settings
from backend.settings import *  # noqa: F401, F403

# Use SQLite for Django's internal test runner tables (no MongoDB needed for unit tests)
# The test_* model tests themselves mock all ORM calls.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Silence migration noise during tests
MIGRATION_MODULES = {app: None for app in INSTALLED_APPS}
