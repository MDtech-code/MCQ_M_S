from celery import shared_task
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from apps.accounts.models import User, EmailVerificationToken, PasswordResetToken, ApprovalRequest
from apps.accounts.config.roles import RoleRegistry
from apps.common.services.email_service import EmailService
from apps.notifications.models import Notification
from apps.common.choices.role import Role
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(bind=True, max_retries=3)
def send_notification_task(self, user_id, message, notification_type=Notification.NotificationType.GENERAL):
    """Create a notification for the specified user."""
    logger.info(f"Starting task to send notification for User ID: {user_id}")
    try:
        user = User.objects.get(id=user_id)
        Notification.objects.create(
            user=user, 
            message=message, 
            notification_type=notification_type
        )
        logger.info(f"Notification created for user {user.username}: {message}")
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found.")
    except Exception as e:
        logger.error(f"Failed to create notification for user ID {user_id}: {str(e)}")
        self.retry(countdown=60)

@shared_task(bind=True, max_retries=3)
def send_welcome_email_task(self, user_id):
    """Send a welcome email to the user."""
    try:
        user = User.objects.get(id=user_id)
        EmailService.send_email(
            email_type='welcome',
            recipients=[user.email],
            context={
                'user': user,
                'message': RoleRegistry.get_welcome_message(user.role)
            }
        )
        logger.info(f"Welcome email task triggered for user {user.username} (ID: {user_id})")
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found.")
    except Exception as e:
        logger.error(f"Failed to send welcome email to user ID {user_id}: {str(e)}")
        self.retry(countdown=60)

@shared_task
def send_verification_email_task(user_id, token, new_email=None):
    """Send a verification email to the user."""
    try:
        user = User.objects.get(id=user_id)
        token_obj = EmailVerificationToken.objects.get(token=token, user=user)
        if not token_obj.is_valid():
            logger.warning(f"Expired token for {user.email}")
            return
        verify_url = f"{settings.FRONTEND_URL}{reverse('verify_email', args=[token])}"
        EmailService.send_email(
            email_type='verification',
            recipients=[new_email or user.email],
            context={
                'user': user,
                'verify_url': verify_url,
                'token': token
            }
        )
        logger.info(f"Verification email task triggered for user {user.email} (ID: {user_id})")
    except User.DoesNotExist:
        logger.error(f"User ID {user_id} not found")
    except EmailVerificationToken.DoesNotExist:
        logger.error(f"Token {token} not found for user ID {user_id}")
    except Exception as e:
        logger.error(f"Failed to send verification email to user ID {user_id}: {str(e)}")

@shared_task
def send_password_reset_email_task(user_id, token):
    """Send a password reset email to the user."""
    try:
        user = User.objects.get(id=user_id)
        token_obj = PasswordResetToken.objects.get(token=token, user=user)
        if not token_obj.is_valid():
            logger.warning(f"Expired reset token for {user.email}")
            return
        reset_url = f"{settings.FRONTEND_URL}/api/reset-password/{token}/"
        EmailService.send_email(
            email_type='password_reset',
            recipients=[user.email],
            context={
                'user': user,
                'reset_url': reset_url
            }
        )
        logger.info(f"Password reset email task triggered for user {user.email} (ID: {user_id})")
    except User.DoesNotExist:
        logger.error(f"User ID {user_id} not found")
    except PasswordResetToken.DoesNotExist:
        logger.error(f"Reset token {token} not found for user ID {user_id}")
    except Exception as e:
        logger.error(f"Failed to send reset email to user ID {user_id}: {str(e)}")

@shared_task
def send_deletion_confirmation_email_task(email, role):
    """Send an account deletion confirmation email."""
    try:
        message = (
            f"Your student account ({email}) has been permanently deleted from the MCQ Test System.\n"
            f"All associated data has been removed as per your request."
        ) if role == Role.STUDENT else (
            f"Your {role.lower()} account ({email}) has been deactivated.\n"
            f"Your contributions (e.g., tests, questions) remain available.\n"
            f"You can reactivate your account by contacting support."
        )
        EmailService.send_email(
            email_type='deletion_confirmation',
            recipients=[email],
            context={'role': role, 'message': message}
        )
        logger.info(f"Deletion confirmation email task triggered for {email}")
    except Exception as e:
        logger.error(f"Failed to send deletion confirmation to {email}: {str(e)}")

@shared_task(bind=True, max_retries=3)
def send_approval_request_notification(self, approval_request_id):
    """Send a notification to admins about a new teacher approval request."""
    try:
        approval_request = ApprovalRequest.objects.get(id=approval_request_id)
        admins = User.objects.filter(role=Role.ADMIN, is_active=True)
        if not admins.exists():
            logger.warning("No active admins found for approval request notification.")
            return
        changelist = reverse('admin:accounts_approvalrequest_changelist')
        login_url = f"{settings.FRONTEND_URL.rstrip('/')}/admin/login/?next={changelist}"
        EmailService.send_email(
            email_type='approval_request',
            recipients=[admin.email for admin in admins],
            context={
                'approval_request': approval_request,
                'user': approval_request.user,
                'admin_login_url': login_url
            }
        )
        logger.info(f"Approval request email task triggered for ApprovalRequest ID: {approval_request_id}")
    except ApprovalRequest.DoesNotExist:
        logger.error(f"ApprovalRequest with ID {approval_request_id} not found.")
    except Exception as e:
        logger.error(f"Failed to send approval request email for ApprovalRequest ID {approval_request_id}: {str(e)}")
        self.retry(countdown=60)

@shared_task
def send_teacher_approval_email_task(user_id, approved=True):
    """Send a teacher approval status email."""
    try:
        user = User.objects.get(id=user_id)
        notification_message = (
            "Your teacher credentials have been approved."
            if approved else
            "Your teacher credentials were rejected. Please check details and resubmit."
        )
        EmailService.send_email(
            email_type='teacher_approval',
            recipients=[user.email],
            context={
                'user': user,
                'approved': approved,
                'dashboard_url': f"{settings.FRONTEND_URL}/teacher/dashboard/" if approved else None
            }
        )
        send_notification_task.delay(
            user.id,
            notification_message,
            notification_type=Notification.NotificationType.TEACHER_APPROVAL
        )
        logger.info(f"Teacher approval email task triggered (approved={approved}) for user {user.email} (ID: {user_id})")
    except User.DoesNotExist:
        logger.error(f"User ID {user_id} not found")
    except Exception as e:
        logger.error(f"Failed to send approval email to user ID {user_id}: {str(e)}")

# from celery import shared_task
# from django.core.mail import EmailMessage
# from django.contrib.auth import get_user_model
# from django.conf import settings
# from django.urls import reverse
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from .models import User, EmailVerificationToken,PasswordResetToken,ApprovalRequest
# from apps.notifications.models import Notification

# import smtplib
# import logging

# logger = logging.getLogger(__name__)
# User = get_user_model()


# @shared_task(bind=True, max_retries=3)
# def send_notification_task(self, user_id, message, notification_type=Notification.NotificationType.GENERAL):
#     logger.info(f"Starting task to send notification for User ID: {user_id}")
#     try:
#         user = User.objects.get(id=user_id)
#         Notification.objects.create(
#             user=user, 
#             message=message, 
#             notification_type=notification_type
#         )
#         logger.info(f"Notification created for user {user.username}: {message}")
#     except User.DoesNotExist:
#         logger.error(f"User with ID {user_id} not found.")
#     except Exception as e:
#         logger.error(f"Failed to create notification for user ID {user_id}: {str(e)}")
#         self.retry(countdown=60)

        
# @shared_task(bind=True, max_retries=3)
# def send_welcome_email_task(self,user_id):
#     logger.info(f"Celery task using email settings: {settings.EMAIL_HOST}, {settings.EMAIL_PORT}, {settings.EMAIL_HOST_USER}, {settings.EMAIL_USE_TLS}")
#     try:
#         user = User.objects.get(id=user_id)
#         subject = f"Welcome to Our Platform, {user.username}!"
#         message = (
#             f"Hi {user.username},\n\n"
#             f"Thank you for signing up as a {user.get_role_display()} on Our Platform!\n"
#         )
#         if user.role == User.Role.STUDENT:
#             message += "We’re excited to have you join our student community. Start exploring your courses today!\n"
#         elif user.role == User.Role.TEACHER:
#             message += "Awaiting admin approval. You’ll be notified once approved.\n"
#         elif user.role == User.Role.ADMIN:
#             message += "Welcome, administrator! Your responsibilities are key to our success.\n"
#         message += (
#             "\nBest regards,\n"
#             "The Our Platform Team\n"
#             "https://yourplatform.com"
#         )

#         from_email = settings.DEFAULT_FROM_EMAIL
#         recipient_list = [user.email]
#         logger.info(f"Attempting to send welcome email to {recipient_list} (User ID: {user_id}, Username: {user.username})")

#         email = EmailMessage(
#             subject=subject,
#             body=message,
#             from_email=from_email,
#             to=recipient_list,
#             reply_to=[from_email],
#         )
#         email.content_subtype = "plain"
#         result = email.send(fail_silently=False)
#         logger.info(f"Email sent to user {user.username} (ID: {user_id}) with role: {user.role}, result: {result}")
#     except User.DoesNotExist:
#         logger.error(f"User with ID {user_id} not found.")
#     except smtplib.SMTPRecipientsRefused as e:
#         logger.error(f"Recipient refused for user {user_id}: {str(e)}")
#     except smtplib.SMTPException as e:
#         logger.error(f"SMTP error sending welcome email to user {user_id}: {str(e)}")
#     except Exception as e:
#         logger.error(f"General error sending welcome email to user {user_id}: {str(e)}")  
#     except smtplib.SMTPException as e:
#         logger.error(f"SMTP error, retrying... {str(e)}")
#         self.retry(countdown=60)  








# @shared_task
# def send_verification_email_task(user_id, token, new_email=None):
#     try:
#         user = User.objects.get(id=user_id)
#         token_obj = EmailVerificationToken.objects.get(token=token, user=user)
#         if not token_obj.is_valid():
#             logger.warning(f"Expired token for {user.email}")
#             return
#         verify_url = f"{settings.FRONTEND_URL}{reverse('verify_email', args=[token])}"
#         subject = "Verify Your Email Address"
#         email_target = new_email or user.email
#         message = (
#             f"Hi {user.username},\n\n"
#             f"Please verify your email ({email_target}) by clicking the link below:\n"
#             f"{verify_url}\n\n"
#             f"The link expires in 24 hours.\n\n"
#             f"Thanks,\nMCQ Test Team"
#         )
#         email = EmailMessage(
#             subject=subject,
#             body=message,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[email_target],
#         )
#         email.content_subtype = "plain"
#         email.send()
#         logger.info(f"Verification email sent to {email_target}")
#     except User.DoesNotExist:
#         logger.error(f"User ID {user_id} not found")
#     except EmailVerificationToken.DoesNotExist:
#         logger.error(f"Token {token} not found for user ID {user_id}")
#     except Exception as e:
#         logger.error(f"Failed to send verification email to user ID {user_id}: {str(e)}")




# # apps/accounts/tasks.py
# @shared_task
# def send_password_reset_email_task(user_id, token):
#     print(user_id,token)
#     try:
#         user = User.objects.get(id=user_id)
#         token_obj = PasswordResetToken.objects.get(token=token, user=user)
#         if not token_obj.is_valid():
#             logger.warning(f"Expired reset token for {user.email}")
#             return
#         # reset_url = f"{settings.FRONTEND_URL}{reverse('reset_password')}?token={token}"
#         reset_url = f"{settings.FRONTEND_URL}/api/reset-password/{token}/"
#         subject = "Reset Your Password"
#         message = (
#             f"Hi {user.username},\n\n"
#             f"Click the link below to reset your password:\n"
#             f"{reset_url}\n\n"
#             f"The link expires in 1 hour.\n\n"
#             f"If you didn’t request this, ignore this email.\n\n"
#             f"Thanks,\nYour MCQ Test Team"
#         )
#         email = EmailMessage(
#             subject=subject,
#             body=message,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[user.email],
#         )
#         email.content_subtype = "plain"
#         email.send()
#         logger.info(f"Password reset email sent to {user.email}")
#     except User.DoesNotExist:
#         logger.error(f"User ID {user_id} not found")
#     except PasswordResetToken.DoesNotExist:
#         logger.error(f"Reset token {token} not found for user ID {user_id}")
#     except Exception as e:
#         logger.error(f"Failed to send reset email to user ID {user_id}: {str(e)}")



# @shared_task
# def send_deletion_confirmation_email_task(email, role):
#     try:
#         subject = "Account Deletion Confirmation"
#         if role == "ST":
#             message = (
#                 f"Dear User,\n\n"
#                 f"Your student account ({email}) has been permanently deleted from the MCQ Test System.\n"
#                 f"All associated data has been removed as per your request.\n\n"
#                 f"Thank you for using our platform.\n"
#                 f"MCQ Test Team"
#             )
#         else:
#             message = (
#                 f"Dear {role},\n\n"
#                 f"Your {role.lower()} account ({email}) has been deactivated.\n"
#                 f"Your contributions (e.g., tests, questions) remain available.\n"
#                 f"You can reactivate your account by contacting support.\n\n"
#                 f"Thank you,\n"
#                 f"MCQ Test Team"
#             )
#         email_msg = EmailMessage(
#             subject=subject,
#             body=message,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[email],
#         )
#         email_msg.content_subtype = "plain"
#         email_msg.send()
#         logger.info(f"Deletion confirmation email sent to {email}")
#     except Exception as e:
#         logger.error(f"Failed to send deletion confirmation to {email}: {str(e)}")




# @shared_task(bind=True, max_retries=3)
# def send_approval_request_notification(self, approval_request_id):
#     logger.info(f"Starting task to send approval request notification for ApprovalRequest ID: {approval_request_id}")
#     try:
#         approval_request = ApprovalRequest.objects.get(id=approval_request_id)
#         admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
#         if not admins.exists():
#             logger.warning("No active admins found to receive approval request notification.")
#             return

#         # 1) reverse the admin changelist for ApprovalRequest
#         changelist = reverse('admin:accounts_approvalrequest_changelist')
#         # 2) build a login URL that sends the admin straight there
#         login_with_next = (
#             f"{settings.FRONTEND_URL.rstrip('/')}/admin/login/"
#             f"?next={changelist}"
#         )

#         subject = "New Teacher Approval Request"
#         html_message = render_to_string('accounts/new_approval_request.html', {
#             'approval_request': approval_request,
#             'admin_login_url': login_with_next,

#             'user': approval_request.user
#         })

#         from_email = settings.DEFAULT_FROM_EMAIL
#         recipient_list = [admin.email for admin in admins]
#         logger.info(f"Attempting to send approval request email to {recipient_list} for ApprovalRequest ID: {approval_request_id}")

#         email = EmailMessage(
#             subject=subject,
#             body=html_message,
#             from_email=from_email,
#             to=recipient_list,
#             reply_to=[from_email],
#         )
#         email.content_subtype = "html"
#         result = email.send(fail_silently=False)
#         logger.info(f"Approval request email sent for ApprovalRequest ID: {approval_request_id} to {recipient_list}, result: {result}")
#     except ApprovalRequest.DoesNotExist:
#         logger.error(f"ApprovalRequest with ID {approval_request_id} not found.")
#     except smtplib.SMTPRecipientsRefused as e:
#         logger.error(f"Recipient refused for ApprovalRequest ID {approval_request_id}: {str(e)}")
#     except smtplib.SMTPException as e:
#         logger.error(f"SMTP error sending approval request email for ApprovalRequest ID {approval_request_id}: {str(e)}")
#         self.retry(countdown=60)
#     except Exception as e:
#         logger.error(f"General error sending approval request email for ApprovalRequest ID {approval_request_id}: {str(e)}")

# @shared_task
# def send_teacher_approval_email_task(user_id, approved=True):
#     try:
#         user = User.objects.get(id=user_id)
#         subject = "Teacher Account Approval Status"
#         if approved:
#             message = (
#                 f"Dear {user.username},\n\n"
#                 f"Congratulations! Your teacher account has been approved.\n"
#                 f"You can now create and manage tests.\n\n"
#                 f"Visit: {settings.FRONTEND_URL}/teacher/dashboard/\n\n"
#                 f"Thanks,\nMCQ Test Team"
#             )
#             notification_message = "Your teacher credentials have been approved."
#         else:
#             message = (
#                 f"Dear {user.username},\n\n"
#                 f"We regret to inform you that your teacher account application was not approved.\n"
#                 f"For further details, contact support.\n\n"
#                 f"Thanks,\nMCQ Test Team"
#             )
#             notification_message = "Your teacher credentials were rejected. Please check details and resubmit."
#         email = EmailMessage(
#             subject=subject,
#             body=message,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[user.email],
#         )
#         email.content_subtype = "plain"
#         email.send()
#         logger.info(f"Teacher approval email (approved={approved}) sent to {user.email}")
#         # Trigger notification
#         send_notification_task.delay(
#             user.id, 
#             notification_message, 
#             notification_type=Notification.NotificationType.TEACHER_APPROVAL
#         )
#         logger.info(f"Notification queued for user {user.username} on approval status change")
#     except User.DoesNotExist:
#         logger.error(f"User ID {user_id} not found")
#     except Exception as e:
#         logger.error(f"Failed to send approval email to user ID {user_id}: {str(e)}")



