from django.dispatch import Signal, receiver
from django.contrib.auth.models import Group
from apps.accounts.models import ApprovalRequest, EmailVerificationToken
from apps.accounts.config.roles import RoleRegistry
from apps.common.choices.role import Role
from apps.accounts.tasks import send_welcome_email_task,send_verification_email_task,send_approval_request_notification
from apps.accounts.models import User
from django.db.models.signals import post_save
from apps.accounts.service.role_service import RoleService
from apps.accounts.service.profile_service import ProfileService
import logging



logger = logging.getLogger(__name__)


# Define custom signals
user_role_assigned = Signal()  # Sent when a user's role is assigned
profile_created = Signal()      # Sent when a profile is created for a user
approval_request_needed = Signal()  # Sent when an approval request is needed


@receiver(post_save, sender=User)
def handle_user_post_save(sender, instance: User, created: bool, **kwargs) -> None:
    """Handle post-save actions for User model."""
    RoleService.handle_user_creation(instance, created)
    if not created:
        ProfileService.invalidate_profile_cache(instance)
        

@receiver(user_role_assigned, sender=User)
def handle_group_assignment(sender, user: User, **kwargs) -> None:
    """Assign groups to a user based on their role."""
    group_names = RoleRegistry.get_groups(user.role)
    for group_name in group_names:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        logger.info("Assigned group %s to user %s", group_name, user.username)

@receiver(profile_created, sender=User)
def handle_profile_creation(sender, user: User, **kwargs) -> None:
    """Create a profile for the user based on their role."""
    profile_class = RoleRegistry.get_profile_model(user.role)
    if profile_class:
        profile, created = profile_class.objects.get_or_create(user=user)
        logger.info("Created %s profile for user %s (created: %s)", user.role, user.username, created)
    else:
        logger.warning("No profile class found for role %s for user %s", user.role, user.username)

@receiver(approval_request_needed, sender=User)
def handle_approval_request(sender, user: User, **kwargs) -> None:
    """Create an approval request for users requiring approval (e.g., TEACHER)."""
    if user.role == Role.TEACHER:
        approval_request, created = ApprovalRequest.objects.get_or_create(
            user=user,
            defaults={'status': ApprovalRequest.Status.PENDING}
        )
        if created:
            logger.info("Created approval request for teacher %s", user.username)
            send_approval_request_notification.delay(approval_request.id)

@receiver(user_role_assigned, sender=User)
def handle_verification_email(sender, user: User, **kwargs) -> None:
    """Send a verification email to the user."""
    if user.role != Role.ADMIN:  # Skip for admins
        token = EmailVerificationToken.objects.create(user=user)
        send_verification_email_task.delay(user.id, token.token)
        logger.info("Triggered verification email task for user %s", user.username)
@receiver(user_role_assigned, sender=User)
def handle_welcome_email(sender, user: User, **kwargs) -> None:
    """Send a welcome email to the user."""
    if user.role != Role.ADMIN:  # Skip for admins
        send_welcome_email_task.delay(user.id)
        logger.info("Triggered welcome email task for user %s", user.username)
# # accounts/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import Signal,receiver
# from .models import User
# from apps.accounts.service.role_service import RoleService
# import logging

# logger = logging.getLogger(__name__)
# user_signed_up = Signal()

# @receiver(post_save, sender=User)
# def handle_user_creation(sender, instance, created, **kwargs):
#     logger.info("Received post_save signal for user: %s (ID: %s)", instance.username, instance.id)
#     RoleService.handle_user_creation(instance, created)

# @receiver(user_signed_up)
# def user_signed_up_receiver(sender, user, **kwargs):
#     logger.info("Received user_signed_up signal for user: %s (ID: %s)", user.username, user.id)
#     from .tasks import send_welcome_email_task
#     send_welcome_email_task.delay(user.id)









    
# from django.db.models.signals import post_save, pre_save
# from django.dispatch import receiver,Signal
# from .models import User, StudentProfile, TeacherProfile,EmailVerificationToken,ApprovalRequest
# from apps.accounts.tasks import send_welcome_email_task,send_verification_email_task


# import logging
# logger = logging.getLogger(__name__)


# user_signed_up = Signal()
# @receiver(user_signed_up)
# def user_signed_up_receiver(sender, user, **kwargs):

#     """
#     Handles the user_signed_up signal.

#     This function is triggered when a user successfully signs up.
#     It logs the signup event and queues a task to send a welcome email.
    
#     Args:
#         sender (class): The sender of the signal.
#         user (User): The user instance that was created.
#         **kwargs: Additional keyword arguments passed by the signal.

#     Returns:
#         None
#     """

#     logger.info(f"Received user_signed_up signal for user: {user.username} (ID: {user.id})")
#     send_welcome_email_task.delay(user.id)


# @receiver(post_save, sender=User)
# def handle_user_creation(sender, instance, created, **kwargs):
#     """
#     Create a role-specific profile after user creation.
#     Assign ADMIN role to admin users, otherwise create appropriate profile.
#     """
#     if instance.is_superuser:
#         return
    
#     # Auto-update role for staff users
#     if instance.is_staff and instance.role != User.Role.ADMIN:
#         instance.role = User.Role.ADMIN
#         instance.is_approved = True
#         instance.save()
    
#     # Create profile only for non-ADMIN roles
#     if created:
#         if instance.role == User.Role.TEACHER:
#             instance.is_approved = False
#             instance.save()
#         if instance.role != User.Role.ADMIN:
#             try:
#                 if instance.role == User.Role.STUDENT:
#                     StudentProfile.objects.get_or_create(user=instance)
#                 elif instance.role == User.Role.TEACHER:
#                     TeacherProfile.objects.get_or_create(user=instance)
#                 instance._assign_role_group()
#                 token = EmailVerificationToken.objects.create(user=instance)
#                 send_verification_email_task.delay(instance.id, token.token)
#                 logger.info(f"Triggered verification email for {instance.email}")
#             except Exception as e:
#                 logger.error(f"Profile creation failed for {instance}: {str(e)}")



# @receiver(pre_save, sender=User)
# def update_profile_on_role_change(sender, instance, **kwargs):
#     """
#     Delete the old profile if the user's role has changed.
#     """
#     if instance.pk:
#         try:
#             original = User.objects.get(pk=instance.pk)
#         except User.DoesNotExist:
#             return
#         if original.role != instance.role:
#             if original.role == User.Role.STUDENT:
#                 try:
#                     original.studentprofile.delete()
#                 except StudentProfile.DoesNotExist:
#                     pass
#             elif original.role == User.Role.TEACHER:
#                 try:
#                     original.teacherprofile.delete()
#                 except TeacherProfile.DoesNotExist:
#                     pass




# @receiver(post_save, sender=ApprovalRequest)
# def update_teacher_profile_on_approval(sender, instance, created, **kwargs):
#     if not created and instance.status == ApprovalRequest.Status.APPROVED:
#         teacher_profile = instance.user.teacherprofile
#         teacher_profile.qualifications = instance.qualifications
#         teacher_profile.save()




