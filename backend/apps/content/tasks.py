from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Question, QuestionApproval
from apps.accounts.models import User
import logging
logger = logging.getLogger(__name__)
@shared_task
def send_question_notification_task(question_id, user_email, action):
    try:
        question = Question.objects.get(id=question_id)
        subject = f"Question {action.capitalize()} Notification"
        message = f"Your question '{question.question_text[:50]}' has been {action}."
        send_mail(subject, message, 'from@example.com', [user_email])
    except Question.DoesNotExist:
        pass

@shared_task
def notify_admin_approval_task(question_id, flag_reason):
    try:
        question = Question.objects.get(id=question_id)
        subject = "New Question Needs Review"
        message = f"Question '{question.question_text[:50]}' (ID: {question_id}) was flagged: {flag_reason}. Please review."
        admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
        admin_emails = [admin.email for admin in admins]
        send_mail(subject, message, 'from@example.com', admin_emails)
    except Question.DoesNotExist:
        pass

@shared_task
def auto_approve_questions_task():
    threshold = timezone.now() - timedelta(hours=24)
    pending_approvals = QuestionApproval.objects.filter(
        status='PENDING',
        flagged_by_system=False,
        created_at__lte=threshold
    )
    for approval in pending_approvals:
        approval.status = 'APPROVED'
        approval.reviewed_at = timezone.now()
        approval.question.is_active = True
        approval.question.save()
        approval.save()
        logger.info(f"Question {approval.question.id} auto-approved")