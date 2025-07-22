# accounts/services/role_service.py
from django.contrib.auth.models import Group
from apps.accounts.models import User, StudentProfile, TeacherProfile, ApprovalRequest, EmailVerificationToken
from apps.accounts.tasks import send_verification_email_task
import logging

logger = logging.getLogger(__name__)

class RoleService:
    @staticmethod
    def get_profile_class(role):
        profile_map = {
            User.Role.STUDENT: StudentProfile,
            User.Role.TEACHER: TeacherProfile,
        }
        return profile_map.get(role)

    @staticmethod
    def get_role_groups(role):
        group_map = {
            User.Role.STUDENT: ['Student_Group'],
            User.Role.TEACHER: ['Teacher_Group'],
            User.Role.ADMIN: ['Admin_Group'],
        }
        return group_map.get(role, [])

    @staticmethod
    def handle_user_creation(user, created):
        logger.info("Handling user creation for %s (ID: %s, Created: %s)", user.username, user.id, created)
        if user.is_superuser:
            logger.info("Skipping user creation logic for superuser %s", user.username)
            return

        # Handle staff-to-admin conversion
        if user.is_staff and user.role != User.Role.ADMIN:
            user.role = User.Role.ADMIN
            user.is_approved = True
            user.save()
            logger.info("Converted staff user %s to Admin role", user.username)

        if created and user.role != User.Role.ADMIN:
            # Handle teacher approval
            if user.role == User.Role.TEACHER:
                user.is_approved = False
                user.save()
                ApprovalRequest.objects.create(user=user, status=ApprovalRequest.Status.PENDING)
                logger.info("Created approval request for teacher %s", user.username)

            # Create profile
            profile_class = RoleService.get_profile_class(user.role)
            if profile_class:
                profile_class.objects.get_or_create(user=user)
                logger.info("Created %s profile for user %s", user.role, user.username)
            else:
                logger.warning("No profile class found for role %s for user %s", user.role, user.username)

            # Assign groups
            group_names = RoleService.get_role_groups(user.role)
            for group_name in group_names:
                group, _ = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)
                logger.info("Assigned group %s to user %s", group_name, user.username)

            # Send verification email
            token = EmailVerificationToken.objects.create(user=user)
            send_verification_email_task.delay(user.id, token.token)
            logger.info("Triggered verification email for user %s", user.username)