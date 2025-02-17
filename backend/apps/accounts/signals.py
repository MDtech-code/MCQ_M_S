from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User, StudentProfile, TeacherProfile
import logging
logger = logging.getLogger(__name__)

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
        instance.save()
    
    # Create profile only for non-ADMIN roles
    if created and instance.role != User.Role.ADMIN:
        try:
            if instance.role == User.Role.STUDENT:
                StudentProfile.objects.get_or_create(user=instance)
            elif instance.role == User.Role.TEACHER:
                TeacherProfile.objects.get_or_create(user=instance)
        except Exception as e:
            logger.error(f"Profile creation failed for {instance}: {str(e)}")

