
from apps.accounts.serializers import UserSerializer
# from apps.accounts.signals import user_signed_up
from django.contrib.auth import login
from apps.accounts.service.auth_strategies.auth_strategy_interface import AuthStrategy
from django.db import transaction
from typing import Tuple, Optional, Dict, Any
from django.http import HttpRequest
from apps.accounts.models import User
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling user authentication operations.

    This service manages user signup and login using a specified authentication strategy.

    Args:
        strategy: The authentication strategy to use (e.g., CookieTokenAuthStrategy).
    """

    def __init__(self, strategy: AuthStrategy) -> None:
        """Initialize the AuthService with a specific authentication strategy.

        Args:
            strategy: The authentication strategy instance.
        """
        self.strategy = strategy
        logger.debug("AuthService initialized with strategy: %s", strategy.__class__.__name__)

    @transaction.atomic
    def signup(self, request: HttpRequest) -> Tuple[Optional[User], Optional[str], Optional[Dict[str, Any]]]:
        """Handle user signup process.

        Args:
            request: The HTTP request containing user signup data.

        Returns:
            Tuple containing:
                - User instance if created, else None.
                - Authentication token if generated, else None.
                - Errors dictionary if validation fails, else None.
        """
        logger.info("Signup request received with data: %s", request.data)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info("User created successfully: %s (ID: %s)", user.username, user.id)
            # user_signed_up.send(sender=self.__class__, user=user)
            token = self.strategy.generate_token(user)
            if request.accepted_renderer.format == 'html':
                login(request, user, backend='apps.accounts.backends.EmailOrUsernameBackend')
            return user, token, None
        logger.warning("Signup validation errors: %s", serializer.errors)
        return None, None, serializer.errors

    def login(self, request: HttpRequest) -> Tuple[Optional[User], Optional[str], Optional[Dict[str, Any]]]:
        """Handle user login process.

        Args:
            request: The HTTP request containing login credentials.

        Returns:
            Tuple containing:
                - User instance if authenticated, else None.
                - Authentication token if generated, else None.
                - Errors dictionary if authentication fails, else None.
        """
        user, errors = self.strategy.authenticate(request, request.data)
        if user:
            token = self.strategy.generate_token(user)
            if request.accepted_renderer.format == 'html':
                login(request, user, backend='apps.accounts.backends.EmailOrUsernameBackend')
            return user, token, None
        return None, None, errors
# # accounts/services/auth_service.py

# from apps.accounts.serializers import UserSerializer
# from apps.accounts.signals import user_signed_up
# from django.contrib.auth import  login
# from apps.accounts.service.auth_strategies.cookie_token_strategy import CookieTokenAuthStrategy
# from django.db import transaction
# from typing import Tuple, Optional, Dict, Any


# import logging
# logger = logging.getLogger(__name__)






# class AuthService:
#     def __init__(self, strategy=CookieTokenAuthStrategy()):
#         self.strategy = strategy

#     @transaction.atomic
#     def signup(self, request):
#         logger.info("Signup request received with data: %s", request.data)
#         serializer = UserSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             logger.info("User created successfully: %s (ID: %s)", user.username, user.id)
#             user_signed_up.send(sender=self.__class__, user=user)
#             token = self.strategy.generate_token(user)
#             if request.accepted_renderer.format == 'html':
#                 login(request, user, backend='apps.accounts.backends.EmailOrUsernameBackend')
#             return user, token, None
#         logger.warning("Signup validation errors: %s", serializer.errors)
#         return None, None, serializer.errors

#     def login(self, request):
#         user, errors = self.strategy.authenticate(request, request.data)
#         if user:
#             token = self.strategy.generate_token(user)
#             if request.accepted_renderer.format == 'html':
#                 login(request, user, backend='apps.accounts.backends.EmailOrUsernameBackend')
#             return user, token, None
#         return None, None, errors
    


