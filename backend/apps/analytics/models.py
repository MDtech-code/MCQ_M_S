from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import ValidationError
from apps.common.models import TimeStampedModel

class StudentProgress(TimeStampedModel):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    subject = models.ForeignKey('content.Subject', on_delete=models.CASCADE)
    total_attempts = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(
        null=True,
        blank=True,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    strength_topics = models.ManyToManyField('content.Topic', related_name='strengths')
    weakness_topics = models.ManyToManyField('content.Topic', related_name='weaknesses')
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'subject']
        indexes = [
            models.Index(fields=['student', 'subject']),
        ]

    def clean(self):
        from apps.accounts.models import User
        if self.student.role != User.Role.STUDENT:
            raise ValidationError("Only students can have progress records.")

    def update_progress(self):
        from apps.examination.models import TestAttempt
        attempts = TestAttempt.objects.filter(
            student=self.student,
            test__subjects=self.subject,
            score__isnull=False
        )
        self.total_attempts = attempts.count()
        if self.total_attempts > 0:
            self.average_score = attempts.aggregate(models.Avg('score'))['score__avg']
        else:
            self.average_score = 0
        self.save()
        # TODO: Implement logic to update strength_topics and weakness_topics

class TestAnalytics(TimeStampedModel):
    test = models.OneToOneField('examination.Test', on_delete=models.CASCADE)
    average_score = models.FloatField(
        null=True,
        blank=True,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    difficulty_distribution = models.JSONField(default=dict)  # e.g., {"E": 2, "M": 2, "H": 1}
    question_analysis = models.JSONField(default=dict)  # e.g., {"51": {"correct_count": 20, "incorrect_count": 5}}

    class Meta:
        indexes = [
            models.Index(fields=['test']),
        ]

    def update_analytics(self):
        from apps.examination.models import TestAttempt, StudentResponse
        attempts = TestAttempt.objects.filter(test=self.test, score__isnull=False)
        self.average_score = attempts.aggregate(models.Avg('score'))['score__avg'] or 0
        # Difficulty distribution
        questions = self.test.questions.all()
        self.difficulty_distribution = {
            'E': questions.filter(difficulty='E').count(),
            'M': questions.filter(difficulty='M').count(),
            'H': questions.filter(difficulty='H').count()
        }
        # Question analysis
        self.question_analysis = {}
        for q in questions:
            responses = StudentResponse.objects.filter(attempt__test=self.test, question=q)
            self.question_analysis[str(q.id)] = {
                'correct_count': responses.filter(is_correct=True).count(),
                'incorrect_count': responses.filter(is_correct=False).count()
            }
        self.save()


# from django.db import models
# from common.models import TimeStampedModel
# # Create your models here.

# class StudentProgress(TimeStampedModel):
#     student = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
#     subject = models.ForeignKey('content.Subject', on_delete=models.CASCADE)
#     total_attempts = models.PositiveIntegerField(default=0)
#     average_score = models.FloatField()
#     strength_topics = models.ManyToManyField('content.Topic', related_name='strengths')
#     weakness_topics = models.ManyToManyField('content.Topic', related_name='weaknesses')
#     last_updated = models.DateTimeField(auto_now=True)

# class TestAnalytics(TimeStampedModel):
#     test = models.OneToOneField('examination.Test', on_delete=models.CASCADE)
#     average_score = models.FloatField()
#     difficulty_distribution = models.JSONField()
#     question_analysis = models.JSONField()  # { question_id: { correct_count: X, incorrect_count: Y } }
