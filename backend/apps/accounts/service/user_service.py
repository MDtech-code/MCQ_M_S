from typing import Dict, Any,TYPE_CHECKING
from django.contrib.auth import get_user_model

from apps.accounts.models import User
from apps.common.choices.role import Role
import logging

logger = logging.getLogger(__name__)

UserModel = get_user_model()


if TYPE_CHECKING:
    pass
    # Only used by static type checkers, not at runtime

class UserService:
    """Service for handling user creation and management operations.

    This service abstracts user-related operations, decoupling serializers and other
    components from direct interaction with the User model.
    """

    @staticmethod
    def create_user(validated_data: Dict[str, Any]) -> User:
        """Create a new user with the provided validated data.

        Args:
            validated_data: Dictionary containing user data (username, email, password, role).

        Returns:
            The created User instance.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        username = validated_data.get('username')
        email = validated_data.get('email')
        password = validated_data.get('password')
        role = validated_data.get('role', Role.STUDENT)

        if not all([username, email, password]):
            logger.error("Missing required fields for user creation: username=%s, email=%s", username, email)
            raise ValueError("Username, email, and password are required.")

        user = UserModel(
            username=username,
            email=email,
            role=role
        )
        user.set_password(password)
        user.save()
        logger.info("Created new user: username=%s, id=%s, role=%s", user.username, user.id, user.role)
        return user
