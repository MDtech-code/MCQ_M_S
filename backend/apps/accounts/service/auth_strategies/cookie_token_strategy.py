# accounts/services/auth_service.py
from abc import ABC, abstractmethod
from django.forms import ValidationError
from apps.accounts.models import User
from apps.accounts.serializers import  UserLoginSerializer

from apps.accounts.service.security_service import SecurityService
from django.contrib.auth import authenticate, login
from apps.accounts.service.auth_strategies.auth_strategy_interface import AuthStrategy
from django.db import transaction
from apps.accounts.utils.token_utils import get_or_create_token
import logging

logger = logging.getLogger(__name__)



class CookieTokenAuthStrategy(AuthStrategy):
    def authenticate(self, request, data):
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            try:
                SecurityService.limit_login_attempts(username)
                logger.info("Login attempt for username: %s", username)
                user = authenticate(request, username=username, password=password)
                if user:
                    return user, None
                logger.warning("Invalid credentials for username: %s", username)
                return None, {"non_field_errors": ["Invalid credentials"]}
            except ValidationError as e:
                logger.warning("Rate limit error for username %s: %s", username, str(e))
                return None, {"non_field_errors": [str(e)]}
        logger.warning("Login serializer errors: %s", serializer.errors)
        return None, serializer.errors

    def generate_token(self, user):
        token, _ = get_or_create_token(user)
        return token