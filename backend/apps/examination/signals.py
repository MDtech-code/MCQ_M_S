# # apps/examination/signals.py
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from .models import Test
# import logging
# logger = logging.getLogger(__name__)

# @receiver(post_save, sender=Test)
# def log_test_save(sender, instance, created, **kwargs):
#     action = "created" if created else "updated"
#     logger.info(f"Test {instance.id} {action} by {instance.creator.email if instance.creator else 'unknown'}")

# @receiver(post_delete, sender=Test)
# def log_test_delete(sender, instance, **kwargs):
#     logger.info(f"Test {instance.id} deleted by {instance.creator.email if instance.creator else 'unknown'}")from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from apps.examination.models import TestAttempt
from apps.analytics.tasks import update_student_progress, update_test_analytics, record_test_attempt_history

@receiver(post_save, sender=TestAttempt)
def update_analytics(sender, instance, **kwargs):
    print('mia chalt to ra hu')
    if instance.end_time and instance.score is not None:
        # Update TestAnalytics
        update_test_analytics.delay(instance.test.id)
        # Update StudentProgress for each subject
        for subject in instance.test.subjects.all():
            update_student_progress.delay(instance.student.id, subject.id)
        # Record history
        record_test_attempt_history.delay(instance.id)