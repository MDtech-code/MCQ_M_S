from django.db import models
from django.conf import settings

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        TEACHER_APPROVAL = 'TEACHER_APPROVAL', 'Teacher Approval'
        STUDENT_TEST = 'STUDENT_TEST', 'Student Test'
        GENERAL = 'GENERAL', 'General'
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.GENERAL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"