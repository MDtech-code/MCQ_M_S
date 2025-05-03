from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Question, QuestionApproval
from django.template.loader import render_to_string
from apps.accounts.models import User,ApprovalRequest
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


@shared_task
def send_teacher_approval_email_task(user_id, approved):
    user = User.objects.get(id=user_id)
    subject = "Teacher Approval Status"
    message = render_to_string('emails/approval_status.html', {
        'user': user,
        'approved': approved,
        'rejection_reason': ApprovalRequest.objects.filter(user=user).last().rejection_reason if not approved else ''
    })
    send_mail(
        subject,
        message,
        'from@mcqmaster.com',
        [user.email],
        html_message=message
    )



@shared_task
def send_approval_request_notification(approval_request_id):
    approval_request = ApprovalRequest.objects.get(id=approval_request_id)
    admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
    subject = "New Teacher Approval Request"
    message = render_to_string('emails/new_approval_request.html', {
        'approval_request': approval_request,
        'user': approval_request.user
    })
    send_mail(
        subject,
        message,
        'from@mcqmaster.com',
        [admin.email for admin in admins],
        html_message=message
    )