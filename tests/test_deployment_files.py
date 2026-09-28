from pathlib import Path
from unittest import TestCase


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DeploymentFilesTests(TestCase):
    def test_render_blueprint_runs_the_complete_deploy_flow(self):
        blueprint = (PROJECT_ROOT / "render.yaml").read_text()

        self.assertIn("name: mangowit", blueprint)
        self.assertIn("runtime: python", blueprint)
        self.assertIn("plan: free", blueprint)
        self.assertIn("collectstatic --noinput", blueprint)
        self.assertIn("manage.py migrate", blueprint)
        self.assertIn("manage.py seed_ai_data", blueprint)
        self.assertIn("gunicorn mangowit.wsgi:application", blueprint)
        self.assertIn("healthCheckPath: /", blueprint)

    def test_production_commands_have_runtime_dependencies(self):
        requirements = (PROJECT_ROOT / "requirements.txt").read_text().lower()

        for dependency in (
            "cloudinary",
            "dj-database-url",
            "django-cloudinary-storage",
            "gunicorn",
            "psycopg",
            "whitenoise",
        ):
            self.assertIn(dependency, requirements)
