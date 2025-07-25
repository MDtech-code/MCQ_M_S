
from apps.accounts.models import User
from apps.accounts.config.roles import RoleRegistry
from apps.common.choices.role import Role

import logging
from typing import Type, Optional

logger = logging.getLogger(__name__)

class RoleService:
    """Service for handling role-related operations.

    This service manages role-specific tasks such as profile creation, group assignment,
    and user creation logic, using configurations from RoleRegistry.
    """

    @staticmethod
    def get_profile_class(role: str) -> Optional[Type]:
        """Retrieve the profile model class for a given role.

        Args:
            role: The role identifier (e.g., Role.STUDENT).

        Returns:
            The profile model class or None if not applicable.
        """
        return RoleRegistry.get_profile_model(role)

    @staticmethod
    def get_role_groups(role: str) -> list[str]:
        """Retrieve the group names for a given role.

        Args:
            role: The role identifier.

        Returns:
            List of group names associated with the role.
        """
        return RoleRegistry.get_groups(role)

    @staticmethod
    def handle_user_creation(user: User, created: bool) -> None:
        from apps.accounts.signals import user_role_assigned,profile_created,approval_request_needed
        """Handle tasks after user creation, such as profile creation and group assignment.

        Args:
            user: The User instance.
            created: Whether the user was newly created.
        """
        logger.info("Handling user creation for %s (ID: %s, Created: %s)", user.username, user.id, created)
        if user.is_superuser:
            logger.info("Skipping user creation logic for superuser %s", user.username)
            return

        # Handle staff-to-admin conversion
        if user.is_staff and user.role != Role.ADMIN:
            user.role = Role.ADMIN
            user.is_approved = True
            user.save()
            logger.info("Converted staff user %s to Admin role", user.username)

        if created:
            # Dispatch signals for role-specific actions
            user_role_assigned.send(sender=User, user=user)
            profile_created.send(sender=User, user=user)
            approval_request_needed.send(sender=User, user=user)

        # if created and user.role != Role.ADMIN:
        #     # Handle teacher approval
        #     if user.role == Role.TEACHER:
        #         user.is_approved = False
        #         user.save()
        #         ApprovalRequest.objects.create(user=user, status=ApprovalRequest.Status.PENDING)
        #         logger.info("Created approval request for teacher %s", user.username)

        #     # Create profile
        #     profile_class = RoleService.get_profile_class(user.role)
        #     if profile_class:
        #         profile_class.objects.get_or_create(user=user)
        #         logger.info("Created %s profile for user %s", user.role, user.username)
        #     else:
        #         logger.warning("No profile class found for role %s for user %s", user.role, user.username)

        #     # Assign groups
        #     group_names = RoleService.get_role_groups(user.role)
        #     for group_name in group_names:
        #         group, _ = Group.objects.get_or_create(name=group_name)
        #         user.groups.add(group)
        #         logger.info("Assigned group %s to user %s", group_name, user.username)

        #     # Send verification email
        #     token = EmailVerificationToken.objects.create(user=user)
        #     send_verification_email_task.delay(user.id, token.token)
        #     logger.info("Triggered verification email for user %s", user.username)




# # accounts/services/role_service.py
# from django.contrib.auth.models import Group
# from apps.accounts.models import User, StudentProfile, TeacherProfile, ApprovalRequest, EmailVerificationToken
# from apps.accounts.tasks import send_verification_email_task
# import logging

# logger = logging.getLogger(__name__)

# class RoleService:
#     @staticmethod
#     def get_profile_class(role):
#         profile_map = {
#             Role.STUDENT: StudentProfile,
#             Role.TEACHER: TeacherProfile,
#         }
#         return profile_map.get(role)

#     @staticmethod
#     def get_role_groups(role):
#         group_map = {
#             Role.STUDENT: ['Student_Group'],
#             Role.TEACHER: ['Teacher_Group'],
#             Role.ADMIN: ['Admin_Group'],
#         }
#         return group_map.get(role, [])

#     @staticmethod
#     def handle_user_creation(user, created):
#         logger.info("Handling user creation for %s (ID: %s, Created: %s)", user.username, user.id, created)
#         if user.is_superuser:
#             logger.info("Skipping user creation logic for superuser %s", user.username)
#             return

#         # Handle staff-to-admin conversion
#         if user.is_staff and user.role != Role.ADMIN:
#             user.role = Role.ADMIN
#             user.is_approved = True
#             user.save()
#             logger.info("Converted staff user %s to Admin role", user.username)

#         if created and user.role != Role.ADMIN:
#             # Handle teacher approval
#             if user.role == Role.TEACHER:
#                 user.is_approved = False
#                 user.save()
#                 ApprovalRequest.objects.create(user=user, status=ApprovalRequest.Status.PENDING)
#                 logger.info("Created approval request for teacher %s", user.username)

#             # Create profile
#             profile_class = RoleService.get_profile_class(user.role)
#             if profile_class:
#                 profile_class.objects.get_or_create(user=user)
#                 logger.info("Created %s profile for user %s", user.role, user.username)
#             else:
#                 logger.warning("No profile class found for role %s for user %s", user.role, user.username)

#             # Assign groups
#             group_names = RoleService.get_role_groups(user.role)
#             for group_name in group_names:
#                 group, _ = Group.objects.get_or_create(name=group_name)
#                 user.groups.add(group)
#                 logger.info("Assigned group %s to user %s", group_name, user.username)

#             # Send verification email
#             token = EmailVerificationToken.objects.create(user=user)
#             send_verification_email_task.delay(user.id, token.token)
#             logger.info("Triggered verification email for user %s", user.username)