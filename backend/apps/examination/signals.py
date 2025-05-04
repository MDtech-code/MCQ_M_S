from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TestAttempt
from apps.analytics.tasks import update_test_analytics, update_student_progress, record_test_attempt_history
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=TestAttempt)
def update_analytics(sender, instance, **kwargs):
    logger.info('Signal triggered for TestAttempt update')
    if instance.end_time and instance.score is not None:
        logger.info(f'Processing TestAttempt {instance.id} for test {instance.test.id}')
        # Update TestAnalytics
        logger.info('Enqueuing update_test_analytics task')
        update_test_analytics.delay(instance.test.id)
        # Update StudentProgress for the single subject
        if instance.test.subject:
            logger.info(f'Enqueuing update_student_progress task for student {instance.student.id}, subject {instance.test.subject.id}')
            update_student_progress.delay(instance.student.id, instance.test.subject.id)
        else:
            logger.warning('No subject associated with the test')
        # Record history
        logger.info('Enqueuing record_test_attempt_history task')
        record_test_attempt_history.delay(instance.id)
    else:
        logger.info('TestAttempt not complete (missing end_time or score)')