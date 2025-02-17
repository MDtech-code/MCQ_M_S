from django.db import models
from apps.common.models import TimeStampedModel
# Create your models here.
class Subject(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    

class Topic(TimeStampedModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    parent_topic = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    difficulty_level = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict)  # For future expansion

    class Meta:
        unique_together = ('subject', 'name')

class Question(TimeStampedModel):
    DIFFICULTY_CHOICES = (
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard'),
    )
    
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, default='MCQ')
    difficulty = models.CharField(max_length=1, choices=DIFFICULTY_CHOICES)
    topics = models.ManyToManyField(Topic)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    metadata = models.JSONField(default=dict)  # For explanations, references
    
    # Answer structure for MCQs
    options = models.JSONField()
    correct_answer = models.CharField(max_length=1)  # Store option key (A/B/C/D)
    
    # Versioning for question updates
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['difficulty']),
            models.Index(fields=['created_by']),
        ]