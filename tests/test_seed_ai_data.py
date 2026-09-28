from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from AI_communication.models import AIAnswer, AIQuestion


class SeedAIDataCommandTests(TestCase):
    def test_command_is_idempotent(self):
        output = StringIO()

        call_command("seed_ai_data", stdout=output)
        call_command("seed_ai_data", stdout=output)

        self.assertEqual(AIQuestion.objects.count(), 21)
        self.assertEqual(AIAnswer.objects.count(), 21)
        self.assertFalse(
            AIQuestion.objects.filter(aianswer__isnull=True).exists()
        )
        self.assertIn("21", output.getvalue())
