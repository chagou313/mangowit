import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import TestCase


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTING_NAMES = {
    "CLOUDINARY_URL",
    "DATABASE_URL",
    "MANGOWIT_CSRF_TRUSTED_ORIGINS",
    "MANGOWIT_DB_ENGINE",
    "MANGOWIT_DB_NAME",
    "MANGOWIT_DB_USER",
    "MANGOWIT_DB_PASSWORD",
    "MANGOWIT_DB_HOST",
    "MANGOWIT_DB_PORT",
    "MANGOWIT_DEBUG",
}


class RuntimeSettingsTests(TestCase):
    def load_settings(self, names, overrides=None):
        environment = os.environ.copy()
        for name in SETTING_NAMES:
            environment.pop(name, None)
        environment.update(overrides or {})
        names_json = json.dumps(names)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json; "
                    "from django.conf import settings; "
                    f"names = json.loads({names_json!r}); "
                    "print(json.dumps({name: getattr(settings, name) for name in names}, default=str))"
                ),
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def load_databases(self, overrides=None):
        return self.load_settings(["DATABASES"], overrides)["DATABASES"]

    def test_sqlite_is_the_default_database(self):
        databases = self.load_databases()

        self.assertEqual(databases["default"]["ENGINE"], "django.db.backends.sqlite3")
        self.assertTrue(databases["default"]["NAME"].endswith("db.sqlite3"))

    def test_mysql_configuration_comes_from_environment(self):
        databases = self.load_databases(
            {
                "MANGOWIT_DB_ENGINE": "mysql",
                "MANGOWIT_DB_NAME": "mangowit_test",
                "MANGOWIT_DB_USER": "mangowit_user",
                "MANGOWIT_DB_PASSWORD": "test-password",
                "MANGOWIT_DB_HOST": "db.internal",
                "MANGOWIT_DB_PORT": "3307",
            }
        )

        self.assertEqual(
            databases["default"],
            {
                "ENGINE": "django.db.backends.mysql",
                "NAME": "mangowit_test",
                "USER": "mangowit_user",
                "PASSWORD": "test-password",
                "HOST": "db.internal",
                "PORT": "3307",
            },
        )

    def test_database_url_selects_postgresql(self):
        databases = self.load_databases(
            {
                "DATABASE_URL": "postgresql://user:pass@db.example:5432/mangowit",
                "MANGOWIT_DEBUG": "false",
            }
        )

        self.assertEqual(
            databases["default"]["ENGINE"],
            "django.db.backends.postgresql",
        )
        self.assertEqual(databases["default"]["HOST"], "db.example")
        self.assertEqual(databases["default"]["OPTIONS"], {"sslmode": "require"})

    def test_cloudinary_url_selects_cloud_media_storage(self):
        values = self.load_settings(
            ["STORAGES"],
            {"CLOUDINARY_URL": "cloudinary://key:secret@example"},
        )

        self.assertEqual(
            values["STORAGES"]["default"]["BACKEND"],
            "cloudinary_storage.storage.MediaCloudinaryStorage",
        )

    def test_production_enables_secure_proxy_and_cookies(self):
        values = self.load_settings(
            [
                "CSRF_COOKIE_SECURE",
                "CSRF_TRUSTED_ORIGINS",
                "SECURE_PROXY_SSL_HEADER",
                "SESSION_COOKIE_SECURE",
            ],
            {
                "MANGOWIT_CSRF_TRUSTED_ORIGINS": "https://mangowit.onrender.com",
                "MANGOWIT_DEBUG": "false",
            },
        )

        self.assertTrue(values["CSRF_COOKIE_SECURE"])
        self.assertTrue(values["SESSION_COOKIE_SECURE"])
        self.assertEqual(
            values["CSRF_TRUSTED_ORIGINS"],
            ["https://mangowit.onrender.com"],
        )
        self.assertEqual(
            values["SECURE_PROXY_SSL_HEADER"],
            ["HTTP_X_FORWARDED_PROTO", "https"],
        )
