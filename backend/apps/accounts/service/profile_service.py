# accounts/services.py (append to existing file)
from apps.accounts.models import User, StudentProfile, TeacherProfile
from apps.accounts.serializers import StudentProfileSerializer, TeacherProfileSerializer
from apps.accounts.models import User
import logging


logger = logging.getLogger(__name__)
class ProfileFactory:
    @staticmethod
    def get_profile_model(role):
        profile_map = {
            User.Role.STUDENT: StudentProfile,
            User.Role.TEACHER: TeacherProfile,
        }
        return profile_map.get(role)

    @staticmethod
    def get_profile(user):
        profile_class = ProfileFactory.get_profile_model(user.role)
        if profile_class:
            return profile_class.objects.select_related('user').filter(user=user).first()
        logger.warning("No profile found for user %s with role %s", user.username, user.role)
        return None

    @staticmethod
    def get_serializer_class(role):
        serializer_map = {
            User.Role.STUDENT: StudentProfileSerializer,
            User.Role.TEACHER: TeacherProfileSerializer,
        }
        return serializer_map.get(role)

class ProfileService:
    @staticmethod
    def get_profile(user):
        profile = ProfileFactory.get_profile(user)
        if profile:
            serializer_class = ProfileFactory.get_serializer_class(user.role)
            if serializer_class:
                return serializer_class(profile).data
        return None

    @staticmethod
    def update_profile(user, data, files=None):
        profile = ProfileFactory.get_profile(user)
        if not profile:
            logger.warning("Profile update failed: no profile for user %s", user.username)
            return None, {"error": "Profile not found"}
        serializer_class = ProfileFactory.get_serializer_class(user.role)
        if not serializer_class:
            logger.warning("No serializer found for role %s", user.role)
            return None, {"error": "Invalid role"}
        profile_data = data.get('profile', data)
        if files and 'avatar' in files:
            profile_data['avatar'] = files['avatar']
        serializer = serializer_class(profile, data=profile_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info("Profile updated successfully for user %s", user.username)
            return serializer.data, None
        logger.warning("Profile update validation errors for user %s: %s", user.username, serializer.errors)
        return None, serializer.errors