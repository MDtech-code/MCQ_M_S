from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.accounts.models import ApprovalRequest
from notifications.models import Notification
from apps.accounts.tasks import send_notification_task
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ApprovalRequest)
def create_notification_on_approval_request(sender, instance, created, **kwargs):
    if created:
        message = "Your teacher credentials have been submitted and are pending review."
        send_notification_task.delay(
            instance.user.id, 
            message, 
            notification_type=Notification.NotificationType.TEACHER_APPROVAL
        )
        logger.info(f"Notification queued for user {instance.user.username} on ApprovalRequest creation")
    elif instance.status == ApprovalRequest.Status.APPROVED:
        message = "Congratulations! Your teacher credentials have been approved."
        send_notification_task.delay(
            instance.user.id, 
            message, 
            notification_type=Notification.NotificationType.TEACHER_APPROVAL
        )
        logger.info(f"Notification queued for user {instance.user.username} on ApprovalRequest approval")
    elif instance.status == ApprovalRequest.Status.REJECTED:
        message = f"Your teacher credentials were rejected: {instance.rejection_reason or 'No reason provided'}"
        send_notification_task.delay(
            instance.user.id, 
            message, 
            notification_type=Notification.NotificationType.TEACHER_APPROVAL
        )
        logger.info(f"Notification queued for user {instance.user.username} on ApprovalRequest rejection")