
from typing import Optional, Dict, Any, Tuple
from django.core.cache import cache
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.accounts.config.roles import RoleRegistry
from apps.common.choices.role import Role
import logging

logger = logging.getLogger(__name__)

class ProfileService:
    """Service for managing user profiles with caching."""

    CACHE_KEY_PREFIX = "profile:"
    CACHE_TIMEOUT = 1800  # 30 minutes

    @staticmethod
    def get_profile(user: User) -> Optional[Dict[str, Any]]:
        """Retrieve or cache a user profile based on their role."""
        cache_key = f"{ProfileService.CACHE_KEY_PREFIX}{user.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.debug(f"Cache hit for user {user.username} (ID: {user.id})")
            return cached_data

        profile_class = RoleRegistry.get_profile_model(user.role)
        serializer_class = RoleRegistry.get_profile_serializer(user.role)

        if not profile_class or not serializer_class:
            logger.warning(f"No profile class or serializer for role {user.role} for user {user.username}")
            return None

        try:
            profile = profile_class.objects.select_related('user').get(user=user)
            serializer = serializer_class(profile, context={'user': user})
            data = serializer.data
            cache.set(cache_key, data, ProfileService.CACHE_TIMEOUT)
            logger.info(f"Profile cached for user {user.username} (ID: {user.id})")
            return data
        except profile_class.DoesNotExist:
            logger.warning(f"No profile found for user {user.username} with role {user.role}")
            return None

    @staticmethod
    def invalidate_profile_cache(user: User) -> None:
        """Invalidate cached profile data for a user."""
        cache_key = f"{ProfileService.CACHE_KEY_PREFIX}{user.id}"
        cache.delete(cache_key)
        logger.info(f"Invalidated profile cache for user {user.username} (ID: {user.id})")

    @staticmethod
    def get_profile_class(role: str) -> Optional[type]:
        """Retrieve the profile model class for a given role."""
        return RoleRegistry.get_profile_model(role)

    @staticmethod
    def update_profile(user: User, data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Update an existing user profile and cache it."""
        profile_class = RoleRegistry.get_profile_model(user.role)
        serializer_class = RoleRegistry.get_profile_serializer(user.role)

        if not profile_class or not serializer_class:
            logger.error(f"No profile class or serializer for role {user.role} for user id={user.id}")
            return None, {"error": "Invalid role or missing profile configuration"}

        try:
            profile = profile_class.objects.get(user=user)
            serializer = serializer_class(
                instance=profile,
                data=data,
                context={'user': user},
                partial=True
            )
            if serializer.is_valid():
                profile = serializer.save()
                cache_key = f"{ProfileService.CACHE_KEY_PREFIX}{user.id}"
                cache.set(cache_key, serializer.data, ProfileService.CACHE_TIMEOUT)
                logger.info(f"Updated and cached profile for user {user.username} (ID: {user.id})")
                return serializer.data, None
            else:
                logger.warning(f"Profile validation errors for user id={user.id}: {serializer.errors}")
                return None, serializer.errors
        except profile_class.DoesNotExist:
            logger.error(f"No profile found for user id={user.id} with role {user.role}")
            return None, {"error": "Profile not found"}
        except Exception as e:
            logger.error(f"Failed to update profile for user id={user.id}: {str(e)}")
            return None, {"error": str(e)}
# from typing import Optional, Dict, Any
# from django.core.cache import cache
# from django.core.exceptions import ValidationError
# from apps.accounts.models import User
# from apps.accounts.config.roles import RoleRegistry
# from apps.common.choices.role import Role
# import logging
# logger = logging.getLogger(__name__)

# class ProfileService:    
#     """Service for managing user profiles with caching."""
#     CACHE_KEY_PREFIX = "profile:"
#     CACHE_TIMEOUT = 1800  # 30 minutes

#     @staticmethod
#     def get_profile(user: User) -> Optional[Dict[str, Any]]:
#         """Retrieve or cache a user profile based on their role."""
#         cache_key = f"{ProfileService.CACHE_KEY_PREFIX}{user.id}"
#         cached_data = cache.get(cache_key)
#         if cached_data:
#             logger.debug(f"Cache hit for user {user.username} (ID: {user.id})")
#             return cached_data
#         profile_class = RoleRegistry.get_profile_model(user.role)
#         serializer_class = RoleRegistry.get_profile_serializer(user.role)
#         if not profile_class or not serializer_class:
#             logger.warning(f"No profile class or serializer for role {user.role} for user {user.username}")
#             return None
#         try:
#             profile = profile_class.objects.select_related('user').get(user=user)
#             serializer = serializer_class(profile, context={'user': user})
#             data = serializer.data
#             cache.set(cache_key, data, ProfileService.CACHE_TIMEOUT)
#             logger.info(f"Profile cached for user {user.username} (ID: {user.id})")
#             return data
#         except profile_class.DoesNotExist:
#             logger.warning(f"No profile found for user {user.username} with role {user.role}")
#             return None
#     @staticmethod
#     def invalidate_profile_cache(user: User) -> None:
#         """Invalidate cached profile data for a user."""
#         cache_key = f"{ProfileService.CACHE_KEY_PREFIX}{user.id}"
#         cache.delete(cache_key)
#         logger.info(f"Invalidated profile cache for user {user.username} (ID: {user.id})")
#     @staticmethod
#     def get_profile_class(role: str) -> Optional[type]:
#         """Retrieve the profile model class for a given role."""
#         return RoleRegistry.get_profile_model(role)
#     @staticmethod
#     def update_profile(user: User, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
#         """Update an existing user profile and cache it."""
#         profile_class = RoleRegistry.get_profile_model(user.role)
#         serializer_class = RoleRegistry.get_profile_serializer(user.role)

#         if not profile_class or not serializer_class:
#             logger.error(f"No profile class or serializer for role {user.role} for user id={user.id}")
#             return None

#         try:
#             profile = profile_class.objects.get(user=user)
#             serializer = serializer_class(
#                 instance=profile,
#                 data=data,
#                 files=files or {},
#                 context={'user': user},
#                 partial=True
#             )
#             serializer.is_valid(raise_exception=True)
#             profile = serializer.save()
#             cache_key = f"{ProfileService.CACHE_KEY_PREFIX}{user.id}"
#             cache.set(cache_key, serializer.data, ProfileService.CACHE_TIMEOUT)
#             logger.info(f"Updated and cached profile for user {user.username} (ID: {user.id})")
#             return serializer.data
#         except profile_class.DoesNotExist:
#             logger.error(f"No profile found for user id={user.id} with role {user.role}")
#             return None
#         except ValidationError as e:
#             logger.error(f"Failed to update profile for user id={user.id}: {str(e)}")
#             raise




# from apps.accounts.models import User
# from apps.accounts.config.roles import RoleRegistry
# import logging
# from typing import Optional, Dict, Any, Union

# logger = logging.getLogger(__name__)

# class ProfileFactory:
#     """Factory for retrieving profile models and serializers based on user role."""

#     @staticmethod
#     def get_profile_model(role: str):
#         """Retrieve the profile model for a given role.

#         Args:
#             role: The role identifier (e.g., Role.STUDENT).

#         Returns:
#             The profile model class or None if not applicable.
#         """
#         return RoleRegistry.get_profile_model(role)

#     @staticmethod
#     def get_profile(user: User):
#         """Retrieve the profile instance for a given user.

#         Args:
#             user: The User instance.

#         Returns:
#             The profile instance or None if not found.
#         """
#         profile_class = ProfileFactory.get_profile_model(user.role)
#         if profile_class:
#             return profile_class.objects.select_related('user').filter(user=user).first()
#         logger.warning("No profile found for user %s with role %s", user.username, user.role)
#         return None

#     @staticmethod
#     def get_serializer_class(role: str):
#         """Retrieve the serializer class for a given role.

#         Args:
#             role: The role identifier.

#         Returns:
#             The serializer class or None if not applicable.
#         """
#         return RoleRegistry.get_profile_serializer(role)

# class ProfileService:
#     """Service for managing user profiles."""

#     @staticmethod
#     def get_profile(user: User) -> Optional[Dict[str, Any]]:
#         """Retrieve serialized profile data for a user.

#         Args:
#             user: The User instance.

#         Returns:
#             Serialized profile data or None if not found.
#         """
#         profile = ProfileFactory.get_profile(user)
#         if profile:
#             serializer_class = ProfileFactory.get_serializer_class(user.role)
#             if serializer_class:
#                 return serializer_class(profile).data
#         return None

#     @staticmethod
#     def update_profile(user: User, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
#         """Update a user's profile with provided data and files.

#         Args:
#             user: The User instance.
#             data: The data to update the profile.
#             files: Optional file data (e.g., avatar).

#         Returns:
#             Tuple of (serialized profile data, errors).
#         """
#         profile = ProfileFactory.get_profile(user)
#         if not profile:
#             logger.warning("Profile update failed: no profile for user %s", user.username)
#             return None, {"error": "Profile not found"}
#         serializer_class = ProfileFactory.get_serializer_class(user.role)
#         if not serializer_class:
#             logger.warning("No serializer found for role %s", user.role)
#             return None, {"error": "Invalid role"}
#         profile_data = data.get('profile', data)
#         if files and 'avatar' in files:
#             profile_data['avatar'] = files['avatar']
#         serializer = serializer_class(profile, data=profile_data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             logger.info("Profile updated successfully for user %s", user.username)
#             return serializer.data, None
#         logger.warning("Profile update validation errors for user %s: %s", user.username, serializer.errors)
#         return None, serializer.errors
    

# # accounts/services.py (append to existing file)
# from apps.accounts.models import User, StudentProfile, TeacherProfile
# from apps.accounts.serializers import StudentProfileSerializer, TeacherProfileSerializer
# from apps.accounts.models import User
# import logging


# logger = logging.getLogger(__name__)
# class ProfileFactory:
#     @staticmethod
#     def get_profile_model(role):
#         profile_map = {
#             Role.STUDENT: StudentProfile,
#             Role.TEACHER: TeacherProfile,
#         }
#         return profile_map.get(role)

#     @staticmethod
#     def get_profile(user):
#         profile_class = ProfileFactory.get_profile_model(user.role)
#         if profile_class:
#             return profile_class.objects.select_related('user').filter(user=user).first()
#         logger.warning("No profile found for user %s with role %s", user.username, user.role)
#         return None

#     @staticmethod
#     def get_serializer_class(role):
#         serializer_map = {
#             Role.STUDENT: StudentProfileSerializer,
#             Role.TEACHER: TeacherProfileSerializer,
#         }
#         return serializer_map.get(role)

# class ProfileService:
#     @staticmethod
#     def get_profile(user):
#         profile = ProfileFactory.get_profile(user)
#         if profile:
#             serializer_class = ProfileFactory.get_serializer_class(user.role)
#             if serializer_class:
#                 return serializer_class(profile).data
#         return None

#     @staticmethod
#     def update_profile(user, data, files=None):
#         profile = ProfileFactory.get_profile(user)
#         if not profile:
#             logger.warning("Profile update failed: no profile for user %s", user.username)
#             return None, {"error": "Profile not found"}
#         serializer_class = ProfileFactory.get_serializer_class(user.role)
#         if not serializer_class:
#             logger.warning("No serializer found for role %s", user.role)
#             return None, {"error": "Invalid role"}
#         profile_data = data.get('profile', data)
#         if files and 'avatar' in files:
#             profile_data['avatar'] = files['avatar']
#         serializer = serializer_class(profile, data=profile_data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             logger.info("Profile updated successfully for user %s", user.username)
#             return serializer.data, None
#         logger.warning("Profile update validation errors for user %s: %s", user.username, serializer.errors)
#         return None, serializer.errors