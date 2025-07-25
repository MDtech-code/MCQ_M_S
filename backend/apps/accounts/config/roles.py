from __future__ import annotations
from typing import Type, Dict, List, Callable, Optional
from django.core.exceptions import ValidationError

from apps.common.choices.role import Role
from apps.accounts.models import StudentProfile,TeacherProfile
from apps.accounts.serializers import StudentProfileSerializer, TeacherProfileSerializer

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.accounts.models import User
    
    # Only used by static type checkers, not at runtime

class RoleRegistry:
    """Centralized registry for role-specific configurations.

    This class manages role configurations, including associated groups, profile models,
    profile serializers, and validation rules. It supports dynamic registration of new roles
    to ensure extensibility without modifying existing code.

    Attributes:
        _registry (Dict[str, Dict]): Mapping of role identifiers to their configurations.
    """

    _registry: Dict[str, Dict] = {
        Role.STUDENT: {
            'groups': ['Student_Group'],
            'profile_model': StudentProfile,
            'profile_serializer': StudentProfileSerializer,
            'validators': [],
            'welcome_message': 'Welcome, student! Start exploring your courses today.'
        },
        Role.TEACHER: {
            'groups': ['Teacher_Group'],
            'profile_model': TeacherProfile,
            'profile_serializer': TeacherProfileSerializer,
            'validators': [
                lambda user: setattr(user, 'is_approved', False) if user.is_approved is None else None
            ],
            'welcome_message': 'Welcome, teacher! Your account is pending approval.'
        },
        Role.ADMIN: {
            'groups': ['Admin_Group'],
            'profile_model': None,
            'profile_serializer': None,
            'validators': [
                lambda user: user.is_staff or ValidationError("ADMIN role requires staff status.")
            ],
            'welcome_message': 'Welcome, administrator! Your responsibilities are key to our success.'
        }
    }

    @classmethod
    def register_role(
        cls,
        role: str,
        groups: List[str],
        profile_model: Optional[Type] = None,
        profile_serializer: Optional[Type] = None,
        validators: Optional[List[Callable[[User], None]]] = None,
        welcome_message: Optional[str] = None
    ) -> None:
        """Register a new role with its configuration.

        Args:
            role: The role identifier (e.g., User.Role.STUDENT).
            groups: List of group names associated with the role.
            profile_model: The profile model class for the role, if applicable.
            profile_serializer: The serializer class for the profile, if applicable.
            validators: List of validation functions for the role.
            welcome_message: Custom welcome message for the role's email.

        Example:
            RoleRegistry.register_role(
                'GUEST',
                groups=['Guest_Group'],
                profile_model=None,
                profile_serializer=None,
                validators=[lambda user: setattr(user, 'is_active', True)]
                welcome_message='Welcome, guest! Enjoy limited access.'
            )
            )
        """
        cls._registry[role] = {
            'groups': groups,
            'profile_model': profile_model,
            'profile_serializer': profile_serializer,
            'validators': validators or [],
            'welcome_message': welcome_message or 'Welcome to our platform!'
        }

    @classmethod
    def get_groups(cls, role: str) -> List[str]:
        """Retrieve the group names for a given role.

        Args:
            role: The role identifier.

        Returns:
            List of group names associated with the role.
        """
        return cls._registry.get(role, {}).get('groups', [])

    @classmethod
    def get_profile_model(cls, role: str) -> Optional[Type]:
        """Retrieve the profile model for a given role.

        Args:
            role: The role identifier.

        Returns:
            The profile model class or None if not applicable.
        """
        return cls._registry.get(role, {}).get('profile_model')

    @classmethod
    def get_profile_serializer(cls, role: str) -> Optional[Type]:
        """Retrieve the profile serializer for a given role.

        Args:
            role: The role identifier.

        Returns:
            The profile serializer class or None if not applicable.
        """
        return cls._registry.get(role, {}).get('profile_serializer')

    @classmethod
    def get_validators(cls, role: str) -> List[Callable[[User], None]]:
        """Retrieve the validation functions for a given role.

        Args:
            role: The role identifier.

        Returns:
            List of validation functions for the role.
        """
        return cls._registry.get(role, {}).get('validators', [])
    

    @classmethod
    def get_welcome_message(cls, role: str) -> str:
        """Retrieve the welcome message for a given role."""
        return cls._registry.get(role, {}).get('welcome_message', 'Welcome to our platform!')