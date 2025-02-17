from django.db import models
from common.models import TimeStampedModel
# Create your models here.

class StudentProgress(TimeStampedModel):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    subject = models.ForeignKey('content.Subject', on_delete=models.CASCADE)
    total_attempts = models.PositiveIntegerField(default=0)
    average_score = models.FloatField()
    strength_topics = models.ManyToManyField('content.Topic', related_name='strengths')
    weakness_topics = models.ManyToManyField('content.Topic', related_name='weaknesses')
    last_updated = models.DateTimeField(auto_now=True)

class TestAnalytics(TimeStampedModel):
    test = models.OneToOneField('examination.Test', on_delete=models.CASCADE)
    average_score = models.FloatField()
    difficulty_distribution = models.JSONField()
    question_analysis = models.JSONField()  # { question_id: { correct_count: X, incorrect_count: Y } }
