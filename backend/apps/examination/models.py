from django.db import models
from apps.common.models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
# Create your models here.
class Test(TimeStampedModel):
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,related_name='created_tests')
    subjects = models.ManyToManyField('content.Subject')
    questions = models.ManyToManyField('content.Question', related_name='tests')
    duration = models.PositiveIntegerField(default=10)
    max_attempts = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    scoring_scheme = models.JSONField()
    question_filters = models.JSONField(default=dict)
    
    class Meta:
        indexes = [
           
            models.Index(fields=['created_by']),
        ]

   
     
    def validate(self):
        if not self.subjects.exists():
            raise ValidationError("Test must have at least one subject")
        
    def __str__(self):
        return self.title

class TestAttempt(TimeStampedModel):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    
    # Store calculated analytics for quick access
    def validate_performance_metrics(value):
        if not isinstance(value, dict):
            raise ValidationError("Performance metrics must be a dictionary")
    performance_metrics = models.JSONField(default=dict, validators=[validate_performance_metrics])
    
    
    class Meta:
        unique_together = ('student', 'test')
        indexes = [
            models.Index(fields=['student'])
        ]

    def clean(self):
        if self.student.role != 'STUDENT':
            raise ValidationError("Only students can attempt tests.")
        attempts = TestAttempt.objects.filter(test=self.test, student=self.student).count()
        if attempts >= self.test.max_attempts:
            raise ValidationError("Maximum attempts reached.")
        if self.end_time and self.end_time > self.start_time + timedelta(minutes=self.test.duration):
            raise ValidationError(f"End time exceeds test duration of {self.test.duration} minutes.")
        


    def calculate_score(self):
        responses = self.studentresponse_set.all()
        score = 0
        for response in responses:
            if response.is_correct:
                score += self.test.scoring_scheme.get('correct', 1)
            else:
                score += self.test.scoring_scheme.get('incorrect', 0)
        self.score = score
        self.save()
        return score
    
    def __str__(self):
        return f"{self.student.email} - {self.test.title}"

class StudentResponse(TimeStampedModel):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE)
    question = models.ForeignKey('content.Question', on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1)
    is_correct = models.BooleanField()
    time_taken = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    class Meta:
        indexes = [
            models.Index(fields=['attempt']),
            models.Index(fields=['question']),
        ]
    
    def clean(self):
        if self.selected_answer not in self.question.options:
            raise ValidationError("Selected answer must be one of the question options")
        self.is_correct = (self.selected_answer == self.question.correct_answer)
    
    def __str__(self):
        return f"Response to {self.question.id} in attempt {self.attempt.id}"