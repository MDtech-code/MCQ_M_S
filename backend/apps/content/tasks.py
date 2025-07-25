from celery import shared_task
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.content.models import Question, QuestionApproval
from apps.accounts.models import User, ApprovalRequest
from apps.common.choices.role import Role
from apps.common.services.email_service import EmailService
from django.conf import settings

import logging

logger = logging.getLogger(__name__)

@shared_task
def send_question_notification_task(question_id, user_email, action):
    """Send a notification about a question's status."""
    try:
        question = Question.objects.get(id=question_id)
        EmailService.send_email(
            email_type='question_notification',
            recipients=[user_email],
            context={
                'question': question,
                'action': action
            }
        )
        logger.info(f"Question notification task triggered for question ID {question_id} to {user_email}")
    except Question.DoesNotExist:
        logger.error(f"Question ID {question_id} not found")
    except Exception as e:
        logger.error(f"Failed to send question notification for question ID {question_id}: {str(e)}")

@shared_task
def notify_admin_approval_task(question_id, flag_reason):
    """Notify admins about a flagged question needing review."""
    try:
        question = Question.objects.get(id=question_id)
        admins = User.objects.filter(role=Role.ADMIN, is_active=True)
        admin_emails = [admin.email for admin in admins]
        if not admin_emails:
            logger.warning("No active admins found for question approval notification.")
            return
        EmailService.send_email(
            email_type='admin_approval_notification',
            recipients=admin_emails,
            context={
                'question': question,
                'flag_reason': flag_reason
            }
        )
        logger.info(f"Admin approval notification task triggered for question ID {question_id}")
    except Question.DoesNotExist:
        logger.error(f"Question ID {question_id} not found")
    except Exception as e:
        logger.error(f"Failed to send admin approval notification for question ID {question_id}: {str(e)}")

@shared_task
def auto_approve_questions_task():
    """Auto-approve questions pending for more than 24 hours."""
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
    """Send a teacher approval status email."""
    try:
        user = User.objects.get(id=user_id)
        rejection_reason = ApprovalRequest.objects.filter(user=user).last().rejection_reason if not approved else ''
        EmailService.send_email(
            email_type='teacher_approval',
            recipients=[user.email],
            context={
                'user': user,
                'approved': approved,
                'rejection_reason': rejection_reason,
                'dashboard_url': f"{settings.FRONTEND_URL}/teacher/dashboard/" if approved else None
            }
        )
        logger.info(f"Teacher approval email task triggered (approved={approved}) for user {user.email} (ID: {user_id})")
    except User.DoesNotExist:
        logger.error(f"User ID {user_id} not found")
    except Exception as e:
        logger.error(f"Failed to send teacher approval email to user ID {user_id}: {str(e)}")

@shared_task
def send_approval_request_notification(approval_request_id):
    """Send a notification to admins about a new teacher approval request."""
    try:
        approval_request = ApprovalRequest.objects.get(id=approval_request_id)
        admins = User.objects.filter(role=Role.ADMIN, is_active=True)
        admin_emails = [admin.email for admin in admins]
        if not admin_emails:
            logger.warning("No active admins found for approval request notification.")
            return
        changelist = reverse('admin:accounts_approvalrequest_changelist')
        login_url = f"{settings.FRONTEND_URL.rstrip('/')}/admin/login/?next={changelist}"
        EmailService.send_email(
            email_type='approval_request',
            recipients=admin_emails,
            context={
                'approval_request': approval_request,
                'user': approval_request.user,
                'admin_login_url': login_url
            }
        )
        logger.info(f"Approval request email task triggered for ApprovalRequest ID: {approval_request_id}")
    except ApprovalRequest.DoesNotExist:
        logger.error(f"ApprovalRequest with ID {approval_request_id} not found")
    except Exception as e:
        logger.error(f"Failed to send approval request email for ApprovalRequest ID {approval_request_id}: {str(e)}")

# from celery import shared_task
# from django.core.mail import send_mail
# from django.utils import timezone
# from datetime import timedelta
# from .models import Question, QuestionApproval
# from django.template.loader import render_to_string
# from apps.accounts.models import User,ApprovalRequest
# import logging
# logger = logging.getLogger(__name__)
# @shared_task
# def send_question_notification_task(question_id, user_email, action):
#     try:
#         question = Question.objects.get(id=question_id)
#         subject = f"Question {action.capitalize()} Notification"
#         message = f"Your question '{question.question_text[:50]}' has been {action}."
#         send_mail(subject, message, 'from@example.com', [user_email])
#     except Question.DoesNotExist:
#         pass

# @shared_task
# def notify_admin_approval_task(question_id, flag_reason):
#     try:
#         question = Question.objects.get(id=question_id)
#         subject = "New Question Needs Review"
#         message = f"Question '{question.question_text[:50]}' (ID: {question_id}) was flagged: {flag_reason}. Please review."
#         admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
#         admin_emails = [admin.email for admin in admins]
#         send_mail(subject, message, 'from@example.com', admin_emails)
#     except Question.DoesNotExist:
#         pass

# @shared_task
# def auto_approve_questions_task():
#     threshold = timezone.now() - timedelta(hours=24)
#     pending_approvals = QuestionApproval.objects.filter(
#         status='PENDING',
#         flagged_by_system=False,
#         created_at__lte=threshold
#     )
#     for approval in pending_approvals:
#         approval.status = 'APPROVED'
#         approval.reviewed_at = timezone.now()
#         approval.question.is_active = True
#         approval.question.save()
#         approval.save()
#         logger.info(f"Question {approval.question.id} auto-approved")


# @shared_task
# def send_teacher_approval_email_task(user_id, approved):
#     user = User.objects.get(id=user_id)
#     subject = "Teacher Approval Status"
#     message = render_to_string('emails/approval_status.html', {
#         'user': user,
#         'approved': approved,
#         'rejection_reason': ApprovalRequest.objects.filter(user=user).last().rejection_reason if not approved else ''
#     })
#     send_mail(
#         subject,
#         message,
#         'from@mcqmaster.com',
#         [user.email],
#         html_message=message
#     )



# @shared_task
# def send_approval_request_notification(approval_request_id):
#     approval_request = ApprovalRequest.objects.get(id=approval_request_id)
#     admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
#     subject = "New Teacher Approval Request"
#     message = render_to_string('emails/new_approval_request.html', {
#         'approval_request': approval_request,
#         'user': approval_request.user
#     })
#     send_mail(
#         subject,
#         message,
#         'from@mcqmaster.com',
#         [admin.email for admin in admins],
#         html_message=message
#     )