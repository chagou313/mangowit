import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import TestCase


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTING_NAMES = {
    "MANGOWIT_DB_ENGINE",
    "MANGOWIT_DB_NAME",
    "MANGOWIT_DB_USER",
    "MANGOWIT_DB_PASSWORD",
    "MANGOWIT_DB_HOST",
    "MANGOWIT_DB_PORT",
}


class RuntimeSettingsTests(TestCase):
    def load_databases(self, overrides=None):
        environment = os.environ.copy()
        for name in SETTING_NAMES:
            environment.pop(name, None)
        environment.update(overrides or {})
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json; "
                    "from mangowit.settings import DATABASES; "
                    "print(json.dumps(DATABASES, default=str))"
                ),
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

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
