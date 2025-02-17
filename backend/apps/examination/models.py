from django.db import models
from apps.common.models import TimeStampedModel
# Create your models here.
class Test(TimeStampedModel):
    title = models.CharField(max_length=255)
    creator = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    subjects = models.ManyToManyField('content.Subject')
    duration = models.PositiveIntegerField()  # In minutes
    schedule_start = models.DateTimeField()
    schedule_end = models.DateTimeField()
    max_attempts = models.PositiveIntegerField(default=1)
    scoring_scheme = models.JSONField()  # { "correct": 4, "incorrect": -1 }
    
    # Question selection criteria
    question_filters = models.JSONField(default=dict)
    
    class Meta:
        indexes = [
            models.Index(fields=['schedule_start']),
            models.Index(fields=['creator']),
        ]

class TestAttempt(TimeStampedModel):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    
    # Store calculated analytics for quick access
    performance_metrics = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ('student', 'test')

class StudentResponse(TimeStampedModel):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE)
    question = models.ForeignKey('content.Question', on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1)
    is_correct = models.BooleanField()
    time_taken = models.PositiveIntegerField()  # Seconds
    
    class Meta:
        indexes = [
            models.Index(fields=['attempt']),
            models.Index(fields=['question']),
        ]