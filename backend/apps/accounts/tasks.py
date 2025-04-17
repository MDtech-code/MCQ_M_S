from celery import shared_task
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from .models import User, EmailVerificationToken,PasswordResetToken
import smtplib
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(bind=True, max_retries=3)
def send_welcome_email_task(self,user_id):
    logger.info(f"Celery task using email settings: {settings.EMAIL_HOST}, {settings.EMAIL_PORT}, {settings.EMAIL_HOST_USER}, {settings.EMAIL_USE_TLS}")
    try:
        user = User.objects.get(id=user_id)
        subject = f"Welcome to Our Platform, {user.username}!"
        message = (
            f"Hi {user.username},\n\n"
            f"Thank you for signing up as a {user.get_role_display()} on Our Platform!\n"
        )
        if user.role == User.Role.STUDENT:
            message += "We’re excited to have you join our student community. Start exploring your courses today!\n"
        elif user.role == User.Role.TEACHER:
            message += "Thank you for joining us as a teacher. We look forward to your contributions!\n"
        elif user.role == User.Role.ADMIN:
            message += "Welcome, administrator! Your responsibilities are key to our success.\n"
        message += (
            "\nBest regards,\n"
            "The Our Platform Team\n"
            "https://yourplatform.com"
        )

        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        logger.info(f"Attempting to send welcome email to {recipient_list} (User ID: {user_id}, Username: {user.username})")

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list,
            reply_to=[from_email],
        )
        email.content_subtype = "plain"
        result = email.send(fail_silently=False)
        logger.info(f"Email sent to user {user.username} (ID: {user_id}) with role: {user.role}, result: {result}")
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found.")
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipient refused for user {user_id}: {str(e)}")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending welcome email to user {user_id}: {str(e)}")
    except Exception as e:
        logger.error(f"General error sending welcome email to user {user_id}: {str(e)}")  
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error, retrying... {str(e)}")
        self.retry(countdown=60)  








@shared_task
def send_verification_email_task(user_id, token):
    try:
        user = User.objects.get(id=user_id)
        token_obj = EmailVerificationToken.objects.get(token=token, user=user)
        if not token_obj.is_valid():
            logger.warning(f"Expired token for {user.email}")
            return
        # Build verification URL
        verify_url = f"{settings.FRONTEND_URL}{reverse('verify_email')}?token={token}"
        subject = "Verify Your Email Address"
        message = (
            f"Hi {user.username},\n\n"
            f"Please verify your email by clicking the link below:\n"
            f"{verify_url}\n\n"
            f"The link expires in 24 hours.\n\n"
            f"Thanks,\nYour MCQ Test Team"
        )
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.content_subtype = "plain"  # Plain text to avoid spam
        email.send()
        logger.info(f"Verification email sent to {user.email}")
    except User.DoesNotExist:
        logger.error(f"User ID {user_id} not found")
    except EmailVerificationToken.DoesNotExist:
        logger.error(f"Token {token} not found for user ID {user_id}")
    except Exception as e:
        logger.error(f"Failed to send verification email to user ID {user_id}: {str(e)}")




# apps/accounts/tasks.py
@shared_task
def send_password_reset_email_task(user_id, token):
    try:
        user = User.objects.get(id=user_id)
        token_obj = PasswordResetToken.objects.get(token=token, user=user)
        if not token_obj.is_valid():
            logger.warning(f"Expired reset token for {user.email}")
            return
        reset_url = f"{settings.FRONTEND_URL}{reverse('reset_password')}?token={token}"
        subject = "Reset Your Password"
        message = (
            f"Hi {user.username},\n\n"
            f"Click the link below to reset your password:\n"
            f"{reset_url}\n\n"
            f"The link expires in 1 hour.\n\n"
            f"If you didn’t request this, ignore this email.\n\n"
            f"Thanks,\nYour MCQ Test Team"
        )
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.content_subtype = "plain"
        email.send()
        logger.info(f"Password reset email sent to {user.email}")
    except User.DoesNotExist:
        logger.error(f"User ID {user_id} not found")
    except PasswordResetToken.DoesNotExist:
        logger.error(f"Reset token {token} not found for user ID {user_id}")
    except Exception as e:
        logger.error(f"Failed to send reset email to user ID {user_id}: {str(e)}")



@shared_task
def send_deletion_confirmation_email_task(email, role):
    try:
        subject = "Account Deletion Confirmation"
        if role == "ST":
            message = (
                f"Dear User,\n\n"
                f"Your student account ({email}) has been permanently deleted from the MCQ Test System.\n"
                f"All associated data has been removed as per your request.\n\n"
                f"Thank you for using our platform.\n"
                f"MCQ Test Team"
            )
        else:
            message = (
                f"Dear {role},\n\n"
                f"Your {role.lower()} account ({email}) has been deactivated.\n"
                f"Your contributions (e.g., tests, questions) remain available.\n"
                f"You can reactivate your account by contacting support.\n\n"
                f"Thank you,\n"
                f"MCQ Test Team"
            )
        email_msg = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_msg.content_subtype = "plain"
        email_msg.send()
        logger.info(f"Deletion confirmation email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send deletion confirmation to {email}: {str(e)}")