from django.db import models

class AIQuestion(models.Model):
    question_text = models.CharField(max_length=200)
    asked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text

class AIAnswer(models.Model):
    answer_text = models.TextField()
    answered_at = models.DateTimeField(auto_now_add=True)
    question = models.OneToOneField(AIQuestion, on_delete=models.CASCADE)

    def __str__(self):
        return self.answer_text
