from rest_framework.permissions import BasePermission
# Add this to top of permissions.py
from django.contrib.auth import get_user_model
User = get_user_model()


import logging
logger = logging.getLogger(__name__)

class IsTeacher(BasePermission):
    """
    Allows access if user is in Teacher_Group.
    """
    message = "You must be a teacher to perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated access attempt to teacher action")
            return False
        has_group = request.user.groups.filter(name='Teacher_Group').exists()
        if not has_group:
            logger.warning(
                "User %s denied teacher access: in_teacher_group=%s",
                getattr(request.user, 'username', 'anonymous'),
                has_group
            )
        return has_group

class IsApprovedTeacher(BasePermission):
    """
    Allows access if user is in Teacher_Group and is approved.
    """
    message = "You are not approved to perform this action. Please contact the admin."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated access attempt to approved teacher action")
            return False
        has_group = request.user.groups.filter(name='Teacher_Group').exists()
        is_approved = getattr(request.user, 'is_approved', False)
        if not has_group or not is_approved:
            logger.warning(
                "User %s denied approved teacher access: in_teacher_group=%s, is_approved=%s",
                getattr(request.user, 'username', 'anonymous'),
                has_group,
                is_approved
            )
        return has_group and is_approved

class IsAdmin(BasePermission):
    """
    Allows access if user is in Admin_Group.
    """
    message = "You must be an admin to perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated access attempt to admin action")
            return False
        has_group = request.user.groups.filter(name='Admin_Group').exists()
        if not has_group:
            logger.warning(
                "User %s denied admin access: in_admin_group=%s",
                getattr(request.user, 'username', 'anonymous'),
                has_group
            )
        return has_group

class IsStudent(BasePermission):
    """
    Allows access if user is in Student_Group and is verified.
    """
    message = "You must be a verified student to perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated access attempt to student action")
            return False
        has_group = request.user.groups.filter(name='Student_Group').exists()
        is_verified = getattr(request.user, 'is_verified', False)
        if not has_group or not is_verified:
            logger.warning(
                "User %s denied student access: in_student_group=%s, is_verified=%s",
                getattr(request.user, 'username', 'anonymous'),
                has_group,
                is_verified
            )
        return has_group and is_verified

class IsVerified(BasePermission):
    """
    Allows access if user is verified.
    """
    message = "You are not verified to perform this action. Please verify your account."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated access attempt to verified action")
            return False
        is_verified = getattr(request.user, 'is_verified', False)
        if not is_verified:
            logger.warning(
                "User %s denied access: is_verified=%s",
                getattr(request.user, 'username', 'anonymous'),
                is_verified
            )
        return is_verified

class IsNotAuthenticated(BasePermission):
    """
    Allows access only to non-authenticated users.
    """
    def has_permission(self, request, view):
        is_authenticated = request.user.is_authenticated
        if is_authenticated:
            logger.warning(
                "Authenticated user %s denied access to non-authenticated action",
                getattr(request.user, 'username', 'anonymous')
            )
        return not is_authenticated



class RoleBasedProfilePermission(BasePermission):
    """
    Composite permission that requires:
    1. User verification (using IsVerified permission logic)
    2. Role-specific access rules:
        - Students: Must be in Student_Group
        - Teachers: Must be in Teacher_Group and approved
        - Admins: Must be in Admin_Group
    
    Logs detailed access attempts and denials for auditing.
    """
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = request.user
        
        # Reuse IsVerified permission logic
        if not user.is_authenticated:
            logger.warning("Unauthenticated access attempt to role-based action")
            return False
            
        # Leverage IsVerified's verification check with logging
        is_verified = getattr(user, 'is_verified', False)
        print(is_verified)
        if not is_verified:
            logger.warning(
                "User %s denied role access: verification_status=%s",
                getattr(user, 'username', 'anonymous'),
                is_verified
            )
            return False
            
        # Cache groups to minimize database queries
        if not hasattr(user, '_cached_groups'):
            user._cached_groups = set(user.groups.values_list('name', flat=True))
        
        # Check role-specific permissions
        is_student = 'Student_Group' in user._cached_groups
        is_teacher = 'Teacher_Group' in user._cached_groups
        is_admin = 'Admin_Group' in user._cached_groups

        # Student access (only requires group membership)
        if is_student:
            logger.info("User %s granted student access", user.username)
            return True

        # Teacher access (requires approval)
        if is_teacher:
            if user.is_approved:
                logger.info("User %s granted approved teacher access", user.username)
                return True
            logger.warning(
                "User %s denied teacher access: approval_status=%s",
                user.username,
                user.is_approved
            )
            return False

        # Admin access
        if is_admin:
            logger.info("User %s granted admin access", user.username)
            return True

        # No valid role found
        logger.warning(
            "User %s denied access: valid_roles=%s (student:%s, teacher:%s, admin:%s)",
            user.username,
            list(user._cached_groups),
            is_student,
            is_teacher,
            is_admin
        )
        return False





# class RoleBasedProfilePermission(BasePermission):
#     """
#     Allows access based on user role (group membership):
#     - Students: Must be in Student_Group and verified.
#     - Teachers: Must be in Teacher_Group, verified, and approved.
#     - Admins: Must be in Admin_Group and verified.
#     """
#     message = "You do not have permission to perform this action."

#     def has_permission(self, request, view):
#         # Cache user instance to prevent multiple DB hits
#         user = request.user
        
#         if not user.is_authenticated:
#             return False
            
#         # Check verification status
#         if not user.is_verified:
#             return print(' mia chutia hu mujia verifed ni mila  ')
            
            
#         # Cache group check results
#         if not hasattr(user, '_cached_groups'):
#             user._cached_groups = set(user.groups.values_list('name', flat=True))
        
#         # Check group membership
#         return any([
#             'Student_Group' in user._cached_groups,
#             'Teacher_Group' in user._cached_groups and user.is_approved,
#             'Admin_Group' in user._cached_groups
#         ])
    # def has_permission(self, request, view):
    #     if not request.user or not request.user.is_authenticated:
    #         logger.warning("Unauthenticated access attempt to profile update")
    #         return False

    #     # Check if user is verified
    #     is_verified = getattr(request.user, 'is_verified', False)
    #     if not is_verified:
    #         logger.warning(
    #             "User %s denied access: is_verified=%s",
    #             getattr(request.user, 'username', 'anonymous'),
    #             is_verified
    #         )
    #         return False

    #     # Check group membership
    #     is_student = request.user.groups.filter(name='Student_Group').exists()
    #     is_teacher = request.user.groups.filter(name='Teacher_Group').exists()
    #     is_admin = request.user.groups.filter(name='Admin_Group').exists()

    #     # Student: Must be in Student_Group
    #     if is_student:
    #         logger.debug("User %s granted student access", getattr(request.user, 'username', 'anonymous'))
    #         return True

    #     # Teacher: Must be in Teacher_Group and approved
    #     if is_teacher:
    #         is_approved = getattr(request.user, 'is_approved', False)
    #         if is_approved:
    #             logger.debug("User %s granted approved teacher access", getattr(request.user, 'username', 'anonymous'))
    #             return True
    #         logger.warning(
    #             "User %s denied teacher access: is_approved=%s",
    #             getattr(request.user, 'username', 'anonymous'),
    #             is_approved
    #         )
    #         return False

    #     # Admin: Must be in Admin_Group
    #     if is_admin:
    #         logger.debug("User %s granted admin access", getattr(request.user, 'username', 'anonymous'))
    #         return True

    #     # No valid role
    #     logger.warning(
    #         "User %s denied access: is_student=%s, is_teacher=%s, is_admin=%s",
    #         getattr(request.user, 'username', 'anonymous'),
    #         is_student,
    #         is_teacher,
    #         is_admin
    #     )
    #     return False
