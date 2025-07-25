from typing import Dict, Any, Optional, List
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.accounts.config.roles import RoleRegistry
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class EmailService:
    """Service for centralized email composition and sending across apps.

    This service handles email sending with configurable templates, subjects,
    and role-specific content, ensuring consistency and extensibility.
    """

    EMAIL_CONFIGS = {
        'verification': {
            'subject': 'Verify Your Email Address',
            'html_template': 'emails/verification_email.html',
            'text_template': 'emails/verification_email.txt'
        },
        'welcome': {
            'subject': 'Welcome to Our Platform!',
            'html_template': 'emails/welcome_email.html',
            'text_template': 'emails/welcome_email.txt'
        },
        'password_reset': {
            'subject': 'Reset Your Password',
            'html_template': 'emails/password_reset_email.html',
            'text_template': 'emails/password_reset_email.txt'
        },
        'deletion_confirmation': {
            'subject': 'Account Deletion Confirmation',
            'html_template': 'emails/deletion_confirmation_email.html',
            'text_template': 'emails/deletion_confirmation_email.txt'
        },
        'approval_request': {
            'subject': 'New Teacher Approval Request',
            'html_template': 'emails/approval_request_email.html',
            'text_template': 'emails/approval_request_email.txt'
        },
        'teacher_approval': {
            'subject': 'Teacher Account Approval Status',
            'html_template': 'emails/teacher_approval_email.html',
            'text_template': 'emails/teacher_approval_email.txt'
        },
        'question_notification': {
            'subject': 'Question {action} Notification',
            'html_template': 'emails/question_notification_email.html',
            'text_template': 'emails/question_notification_email.txt'
        },
        'admin_approval_notification': {
            'subject': 'New Question Needs Review',
            'html_template': 'emails/admin_approval_notification_email.html',
            'text_template': 'emails/admin_approval_notification_email.txt'
        }
    }

    @staticmethod
    def send_email(
        email_type: str,
        recipients: List[str],
        context: Optional[Dict[str, Any]] = None,
        from_email: Optional[str] = None
    ) -> None:
        """Send an email to the specified recipients based on the email type.

        Args:
            email_type: The type of email (e.g., 'verification', 'welcome').
            recipients: List of recipient email addresses.
            context: Optional context data for template rendering.
            from_email: Optional sender email address (defaults to settings.DEFAULT_FROM_EMAIL).

        Raises:
            ValueError: If the email type is not configured or recipients list is empty.
        """
        if email_type not in EmailService.EMAIL_CONFIGS:
            logger.error("Unknown email type: %s", email_type)
            raise ValueError(f"Unknown email type: {email_type}")
        if not recipients:
            logger.error("No recipients provided for email type: %s", email_type)
            raise ValueError("No recipients provided")

        config = EmailService.EMAIL_CONFIGS[email_type]
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        context = context or {}

        # Add site_name to context
        context.update({'site_name': settings.SITE_NAME})

        # Render templates
        try:
            html_content = render_to_string(config['html_template'], context)
            text_content = render_to_string(config['text_template'], context)
        except Exception as e:
            logger.error("Failed to render templates for email type %s: %s", email_type, str(e))
            raise

        # Create and send email
        email = EmailMultiAlternatives(
            subject=config['subject'].format(**context),
            body=text_content,
            from_email=from_email,
            to=recipients,
            reply_to=[from_email]
        )
        email.attach_alternative(html_content, 'text/html')
        try:
            email.send(fail_silently=False)
            logger.info("Sent %s email to %s", email_type, recipients)
        except Exception as e:
            logger.error("Failed to send %s email to %s: %s", email_type, recipients, str(e))
            raise