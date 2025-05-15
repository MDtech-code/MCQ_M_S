from django.db import models
from apps.common.models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.content.utils.validations import validate_subject_name, validate_topic_name,validate_options as  external_validate_options




class Subject(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, validators=[validate_subject_name])
    description = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=['name'])]

    def clean(self):
        if Subject.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError("Subject with this name already exists")
        
    def __str__(self):
        return self.name

class Topic(TimeStampedModel):
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT,related_name="topics")
    name = models.CharField(max_length=100, validators=[validate_topic_name])
    parent_topic = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,related_name='subtopics')
    metadata = models.JSONField(default=dict)  
    difficulty_level = models.PositiveIntegerField(default=1, validators=[
    MinValueValidator(1),
    MaxValueValidator(5)
])

    class Meta:
        unique_together = ('subject', 'name')
        indexes = [models.Index(fields=['subject'])]
    
    def clean(self):
        if self.parent_topic == self:
            raise ValidationError("Topic cannot be its own parent")
        # Check for deeper circular references
        current = self.parent_topic
        while current:
            if current == self:
                raise ValidationError("Circular topic reference detected")
            current = current.parent_topic
    def __str__(self):
        return f"{self.subject.name} - {self.name}"
    


class Question(TimeStampedModel):
    DIFFICULTY_CHOICES = (
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard'),
    )
    
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, default='MCQ')
    difficulty = models.CharField(max_length=1, choices=DIFFICULTY_CHOICES)
    topics = models.ManyToManyField(Topic,blank=True,related_name="questions")
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,related_name="questions")
    metadata = models.JSONField(default=dict)  
    
    # Answer structure for MCQs
    
    options = models.JSONField(validators=[external_validate_options])
    correct_answer = models.CharField(max_length=1) 
    
    # Versioning for question updates
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=50, default='manual')  # options: 'manual', 'auto_nlp'


    class Meta:
        indexes = [
            models.Index(fields=['created_by', 'difficulty']),
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['created_by']),
            models.Index(fields=['question_type']),
            models.Index(fields=['created_at']),
        ]
    def clean(self):
        if self.correct_answer not in self.options:
            raise ValidationError("Correct answer must be one of the option keys (A, B, C, D)")
    def validate(self):
        if not self.topics.exists():
            raise ValidationError("Question must have at least one topic")
    def __str__(self):
        return self.question_text[:50]
    


class QuestionApproval(TimeStampedModel):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    question = models.OneToOneField('Question', on_delete=models.CASCADE, related_name='approval')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    flagged_by_system = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Approval for Question {self.question.id} ({self.status})"