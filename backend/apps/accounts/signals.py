from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver,Signal
from .models import User, StudentProfile, TeacherProfile,EmailVerificationToken,ApprovalRequest

import logging
from apps.accounts.tasks import send_welcome_email_task,send_verification_email_task
logger = logging.getLogger(__name__)

user_signed_up = Signal()


#Receiver for user_signed_up signal
@receiver(user_signed_up)
def user_signed_up_receiver(sender, user, **kwargs):
    logger.info(f"Received user_signed_up signal for user: {user.username} (ID: {user.id})")
    send_welcome_email_task.delay(user.id)


@receiver(post_save, sender=User)
def handle_user_creation(sender, instance, created, **kwargs):
    """
    Create a role-specific profile after user creation.
    Assign ADMIN role to admin users, otherwise create appropriate profile.
    """
    if instance.is_superuser:
        return
    
    # Auto-update role for staff users
    if instance.is_staff and instance.role != User.Role.ADMIN:
        instance.role = User.Role.ADMIN
        instance.is_approved = True
        instance.save()
    
    # Create profile only for non-ADMIN roles
    if created:
        if instance.role == User.Role.TEACHER:
            instance.is_approved = False
            instance.save()
        if instance.role != User.Role.ADMIN:
            try:
                if instance.role == User.Role.STUDENT:
                    StudentProfile.objects.get_or_create(user=instance)
                elif instance.role == User.Role.TEACHER:
                    TeacherProfile.objects.get_or_create(user=instance)
                    
                token = EmailVerificationToken.objects.create(user=instance)
                send_verification_email_task.delay(instance.id, token.token)
                logger.info(f"Triggered verification email for {instance.email}")
            except Exception as e:
                logger.error(f"Profile creation failed for {instance}: {str(e)}")



@receiver(pre_save, sender=User)
def update_profile_on_role_change(sender, instance, **kwargs):
    """
    Delete the old profile if the user's role has changed.
    """
    if instance.pk:
        try:
            original = User.objects.get(pk=instance.pk)
        except User.DoesNotExist:
            return
        if original.role != instance.role:
            if original.role == User.Role.STUDENT:
                try:
                    original.studentprofile.delete()
                except StudentProfile.DoesNotExist:
                    pass
            elif original.role == User.Role.TEACHER:
                try:
                    original.teacherprofile.delete()
                except TeacherProfile.DoesNotExist:
                    pass




@receiver(post_save, sender=ApprovalRequest)
def update_teacher_profile_on_approval(sender, instance, created, **kwargs):
    if not created and instance.status == ApprovalRequest.Status.APPROVED:
        teacher_profile = instance.user.teacherprofile
        teacher_profile.qualifications = instance.qualifications
        teacher_profile.save()




