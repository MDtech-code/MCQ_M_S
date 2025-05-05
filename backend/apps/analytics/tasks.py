from celery import shared_task
from .models import StudentProgress, TestAnalytics, TestAttemptHistory
from apps.examination.models import TestAttempt
import logging
from apps.examination.models import Test

logger = logging.getLogger(__name__)

@shared_task
def update_student_progress(student_id, subject_id):
    logger.info(f'Starting update_student_progress for student {student_id}, subject {subject_id}')
    try:
        progress = StudentProgress.objects.get(student_id=student_id, subject_id=subject_id)
        logger.debug(f'Found StudentProgress: id={progress.id}, student={progress.student.email}, subject={progress.subject.name}')
        progress.update_progress()
        logger.info(f'Updated StudentProgress {progress.id}: total_attempts={progress.total_attempts}, average_score={progress.average_score}')
    except StudentProgress.DoesNotExist:
        logger.warning(f'No StudentProgress found for student {student_id}, subject {subject_id}')
    except Exception as e:
        logger.error(f'Error in update_student_progress for student {student_id}, subject {subject_id}: {str(e)}')
        raise

@shared_task
def update_test_analytics(test_id):
    logger.info(f'Starting update_test_analytics for test {test_id}')
    try:
        test = Test.objects.get(id=test_id)
        analytics, created = TestAnalytics.objects.get_or_create(test=test)
        logger.debug(f'{"Created" if created else "Found"} TestAnalytics: id={analytics.id}, test={analytics.test.title}')
        analytics.update_analytics()
        logger.info(f'Updated TestAnalytics {analytics.id}: average_score={analytics.average_score}, difficulty_distribution={analytics.difficulty_distribution}')
    except Test.DoesNotExist:
        logger.error(f'No Test found for test {test_id}')
        raise
    except Exception as e:
        logger.error(f'Error in update_test_analytics for test {test_id}: {str(e)}')
        raise
# @shared_task
# def update_test_analytics(test_id):
#     logger.info(f'Starting update_test_analytics for test {test_id}')
#     try:
#         analytics = TestAnalytics.objects.get(test_id=test_id)
#         logger.debug(f'Found TestAnalytics: id={analytics.id}, test={analytics.test.title}')
#         analytics.update_analytics()
#         logger.info(f'Updated TestAnalytics {analytics.id}: average_score={analytics.average_score}, difficulty_distribution={analytics.difficulty_distribution}')
#     except TestAnalytics.DoesNotExist:
#         logger.warning(f'No TestAnalytics found for test {test_id}')
#     except Exception as e:
#         logger.error(f'Error in update_test_analytics for test {test_id}: {str(e)}')
#         raise

@shared_task
def record_test_attempt_history(attempt_id):
    logger.info(f'Starting record_test_attempt_history for attempt {attempt_id}')
    try:
        attempt = TestAttempt.objects.get(id=attempt_id)
        logger.debug(f'Found TestAttempt: id={attempt.id}, student={attempt.student.email}, test={attempt.test.title}, score={attempt.score}')
        history = TestAttemptHistory.objects.create(
            student=attempt.student,
            test=attempt.test,
            score=attempt.score,
            completed_at=attempt.end_time,
            duration=(attempt.end_time - attempt.start_time).total_seconds()
        )
        logger.info(f'Created TestAttemptHistory {history.id} for attempt {attempt_id}')
    except TestAttempt.DoesNotExist:
        logger.warning(f'No TestAttempt found for attempt {attempt_id}')
    except Exception as e:
        logger.error(f'Error in record_test_attempt_history for attempt {attempt_id}: {str(e)}')
        raise
# from celery import shared_task
# from .models import StudentProgress, TestAnalytics
# from apps.examination.models import TestAttempt

# @shared_task
# def update_student_progress(student_id, subject_id):
#     from .models import StudentProgress
#     try:
#         progress = StudentProgress.objects.get(student_id=student_id, subject_id=subject_id)
#         progress.update_progress()
#     except StudentProgress.DoesNotExist:
#         pass

# @shared_task
# def update_test_analytics(test_id):
#     from .models import TestAnalytics
#     try:
#         analytics = TestAnalytics.objects.get(test_id=test_id)
#         analytics.update_analytics()
#     except TestAnalytics.DoesNotExist:
#         pass

# @shared_task
# def record_test_attempt_history(attempt_id):
#     from apps.examination.models import TestAttempt
#     from .models import TestAttemptHistory
#     try:
#         attempt = TestAttempt.objects.get(id=attempt_id)
#         if attempt.score is not None:
#             TestAttemptHistory.objects.create(
#                 student=attempt.student,
#                 test=attempt.test,
#                 score=attempt.score,
#                 completed_at=attempt.end_time,
#                 duration=(attempt.end_time - attempt.start_time).total_seconds()
#             )
#     except TestAttempt.DoesNotExist:
#         pass