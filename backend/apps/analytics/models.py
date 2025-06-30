from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import ValidationError
from apps.common.models import TimeStampedModel
from django.db.models.functions import Upper
import logging

logger = logging.getLogger(__name__)
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
    feedback = models.TextField(blank=True, default='')  # Actionable insights
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
        from apps.examination.models import TestAttempt, StudentResponse
        from apps.content.models import Topic
        logger.debug(f'Updating progress for student {self.student.email}, subject {self.subject.name}')
        attempts = TestAttempt.objects.filter(
            student=self.student,
            test__subject=self.subject,
            score__isnull=False
        )
        logger.debug(f'Found {attempts.count()} attempts')
        self.total_attempts = attempts.count()
        if self.total_attempts > 0:
            self.average_score = attempts.aggregate(models.Avg('score'))['score__avg']
        else:
            self.average_score = 0

        # Update strength and weakness topics
        responses = StudentResponse.objects.filter(
            attempt__in=attempts,
            question__topics__subject=self.subject
        ).select_related('question')
        logger.debug(f'Found {responses.count()} responses')
        
        topic_performance = {}
        for response in responses:
            for topic in response.question.topics.all():
                if topic.id not in topic_performance:
                    topic_performance[topic.id] = {'correct': 0, 'total': 0}
                topic_performance[topic.id]['total'] += 1
                if response.is_correct:
                    topic_performance[topic.id]['correct'] += 1

        self.strength_topics.clear()
        self.weakness_topics.clear()
        feedback_lines = []
        for topic_id, perf in topic_performance.items():
            accuracy = perf['correct'] / perf['total'] if perf['total'] > 0 else 0
            topic = Topic.objects.get(id=topic_id)
            if accuracy >= 0.8:
                self.strength_topics.add(topic)
            elif accuracy < 0.5:
                self.weakness_topics.add(topic)
                feedback_lines.append(f"Review {topic.name} (accuracy: {accuracy:.0%}). Suggested: Study related material in {self.subject.name}.")

        self.feedback = '\n'.join(feedback_lines) or "Keep practicing to identify strengths and weaknesses."
        self.save()
        logger.info(f'Saved StudentProgress: total_attempts={self.total_attempts}, average_score={self.average_score}')
class TestAnalytics(TimeStampedModel):
    test = models.OneToOneField('examination.Test', on_delete=models.CASCADE)
    average_score = models.FloatField(
        null=True,
        blank=True,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    difficulty_distribution = models.JSONField(default=dict)  # e.g., {"E": 2, "M": 2, "H": 1}
    question_analysis = models.JSONField(default=dict)  # e.g., {"51": {"correct_count": 20, "incorrect_count": 5, "common_wrong_answers": {"B": 3}}}
    anomalies = models.JSONField(default=dict)  # e.g., {"51": {"excessive_time_count": 5}}

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

        # Question analysis and anomalies
        self.question_analysis = {}
        self.anomalies = {}
        for q in questions:
            responses = StudentResponse.objects.filter(attempt__test=self.test, question=q)
            correct_count = responses.filter(is_correct=True).count()
            incorrect_count = responses.filter(is_correct=False).count()
            
            # Common wrong answers
            wrong_answers = responses.filter(is_correct=False).values('selected_answer').annotate(
                count=models.Count('selected_answer')
            ).order_by('-count')
            common_wrong = {item['selected_answer']: item['count'] for item in wrong_answers if item['selected_answer']}

            # Anomalies: excessive time (>120s)
            excessive_time_count = responses.filter(time_taken__gt=120).count()

            self.question_analysis[str(q.id)] = {
                'correct_count': correct_count,
                'incorrect_count': incorrect_count,
                'common_wrong_answers': common_wrong
            }
            if excessive_time_count > 0:
                self.anomalies[str(q.id)] = {'excessive_time_count': excessive_time_count}

        self.save()

class TestAttemptHistory(TimeStampedModel):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    test = models.ForeignKey('examination.Test', on_delete=models.CASCADE)
    score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    completed_at = models.DateTimeField()
    duration = models.PositiveIntegerField()  # in seconds

    class Meta:
        indexes = [
            models.Index(fields=['student', 'completed_at']),
            models.Index(fields=['test', 'completed_at']),
        ]

    def clean(self):
        from apps.accounts.models import User
        if self.student.role != User.Role.STUDENT:
            raise ValidationError("Only students can have attempt history.")



