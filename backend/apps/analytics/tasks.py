from celery import shared_task
from .models import StudentProgress, TestAnalytics
from apps.examination.models import TestAttempt

@shared_task
def update_student_progress(student_id, subject_id):
    from .models import StudentProgress
    try:
        progress = StudentProgress.objects.get(student_id=student_id, subject_id=subject_id)
        progress.update_progress()
    except StudentProgress.DoesNotExist:
        pass

@shared_task
def update_test_analytics(test_id):
    from .models import TestAnalytics
    try:
        analytics = TestAnalytics.objects.get(test_id=test_id)
        analytics.update_analytics()
    except TestAnalytics.DoesNotExist:
        pass

@shared_task
def record_test_attempt_history(attempt_id):
    from apps.examination.models import TestAttempt
    from .models import TestAttemptHistory
    try:
        attempt = TestAttempt.objects.get(id=attempt_id)
        if attempt.score is not None:
            TestAttemptHistory.objects.create(
                student=attempt.student,
                test=attempt.test,
                score=attempt.score,
                completed_at=attempt.end_time,
                duration=(attempt.end_time - attempt.start_time).total_seconds()
            )
    except TestAttempt.DoesNotExist:
        pass