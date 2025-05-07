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
    subject = models.ForeignKey('content.Subject', on_delete=models.PROTECT)
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
        if not self.subject and not self.subjects.exists():
            raise ValidationError("Test must have at least one subject")
        
    @property
    def attempt_percentage(self):
        """Calculate attempt progress percentage"""
        if self.max_attempts == 0:
            return 0
        # Get attempts count for current user (student) or all users (teacher)
        attempts_count = self.attempts.count()  # For teacher view
        if hasattr(self, '_prefetched_objects_cache') and 'user_attempts' in self._prefetched_objects_cache:
            attempts_count = len(self.user_attempts)  # For student view
        return min(100, (attempts_count / self.max_attempts) * 100)

    @property
    def difficulty(self):
        """Get highest difficulty level from questions"""
        if hasattr(self, '_prefetched_objects_cache') and 'questions' in self._prefetched_objects_cache:
            difficulties = [q.difficulty for q in self.questions.all()]
        else:
            difficulties = self.questions.values_list('difficulty', flat=True)
        return max(difficulties, default='E')

    
    def get_difficulty_display(self):
        """Human-readable difficulty label"""
        return {
            'E': 'Easy',
            'M': 'Medium',
            'H': 'Hard'
        }[self.difficulty]
        
    def __str__(self):
        return self.title

class TestAttempt(TimeStampedModel):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE,related_name='attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    
    # Store calculated analytics for quick access
    def validate_performance_metrics(value):
        if not isinstance(value, dict):
            raise ValidationError("Performance metrics must be a dictionary")
    performance_metrics = models.JSONField(default=dict, validators=[validate_performance_metrics])
    
    
    class Meta:
        # unique_together = ('student', 'test')
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
        responses = StudentResponse.objects.filter(attempt=self)
        correct_count = responses.filter(is_correct=True).count()
        scoring_scheme = self.test.scoring_scheme or {'correct': 1, 'incorrect': 0}
        self.score = correct_count * scoring_scheme['correct']
    # def calculate_score(self):
    #     responses = self.studentresponse_set.all()
    #     score = 0
    #     for response in responses:
    #         if response.is_correct:
    #             score += self.test.scoring_scheme.get('correct', 1)
    #         else:
    #             score += self.test.scoring_scheme.get('incorrect', 0)
    #     self.score = score
    #     self.save()
    #     return score
    
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