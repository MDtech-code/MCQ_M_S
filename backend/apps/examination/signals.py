from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TestAttempt, Test
from apps.analytics.models import TestAnalytics, StudentProgress
from apps.analytics.tasks import update_test_analytics, update_student_progress, record_test_attempt_history
import logging

logger = logging.getLogger(__name__)

logger.info('Loading examination signals module')
@receiver(post_save, sender=Test)
def create_test_analytics(sender, instance, created, **kwargs):
    logger.info(f'Signal triggered for Test {instance.id} (created: {created})')
    if created:

        try:
            analytics, created = TestAnalytics.objects.get_or_create(test=instance)
            logger.info(f'TestAnalytics {"created" if created else "already exists"} for Test {instance.id}')
        except Exception as e:
            logger.error(f'Failed to create TestAnalytics for Test {instance.id}: {str(e)}')
    

@receiver(post_save, sender=TestAttempt)
def update_analytics(sender, instance, **kwargs):
    logger.info(f'Signal triggered for TestAttempt {instance.id} (created: {kwargs.get("created", False)})')
    logger.debug(f'TestAttempt details: id={instance.id}, end_time={instance.end_time}, score={instance.score}, test_id={instance.test.id}, student_id={instance.student.id}')

    # Check if the instance meets the conditions
    if instance.end_time and instance.score is not None:
        logger.info(f'Processing TestAttempt {instance.id} for test {instance.test.id} (score: {instance.score}, end_time: {instance.end_time})')
        
        # Update TestAnalytics
        logger.info(f'Enqueuing update_test_analytics task for test {instance.test.id}')
        try:
            task = update_test_analytics.delay(instance.test.id)
            logger.info(f'update_test_analytics task enqueued with ID: {task.id}')
        except Exception as e:
            logger.error(f'Failed to enqueue update_test_analytics task: {str(e)}')

        # Update StudentProgress
        if hasattr(instance.test, 'subject') and instance.test.subject:
            logger.info(f'Test has subject: {instance.test.subject.id} ({instance.test.subject.name})')
            logger.info(f'Enqueuing update_student_progress task for student {instance.student.id}, subject {instance.test.subject.id}')
            try:
                # Ensure StudentProgress exists
                progress, created = StudentProgress.objects.get_or_create(
                    student_id=instance.student.id,
                    subject_id=instance.test.subject.id
                )
                if created:
                    logger.info(f'Created StudentProgress for student {instance.student.id}, subject {instance.test.subject.id}')
                task = update_student_progress.delay(instance.student.id, instance.test.subject.id)
                logger.info(f'update_student_progress task enqueued with ID: {task.id}')
            except Exception as e:
                logger.error(f'Failed to enqueue update_student_progress task: {str(e)}')
        else:
            logger.warning(f'No subject associated with test {instance.test.id} or subject is None')

        # Record history
        logger.info(f'Enqueuing record_test_attempt_history task for attempt {instance.id}')
        try:
            task = record_test_attempt_history.delay(instance.id)
            logger.info(f'record_test_attempt_history task enqueued with ID: {task.id}')
        except Exception as e:
            logger.error(f'Failed to enqueue record_test_attempt_history task: {str(e)}')
    else:
        logger.warning(f'TestAttempt {instance.id} not complete: end_time={instance.end_time}, score={instance.score}')
