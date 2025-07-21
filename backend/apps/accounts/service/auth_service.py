# accounts/services.py
from abc import ABC, abstractmethod
from rest_framework.authtoken.models import Token
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer, UserLoginSerializer
from apps.accounts.signals import user_signed_up
from django.contrib.auth import authenticate, login
import logging


logger = logging.getLogger(__name__)


#! abstract class Strategies
class AuthStrategy(ABC):
    @abstractmethod
    def authenticate(self, request, data):
        pass

    @abstractmethod
    def generate_token(self, user):
        pass


#! concrete implementation of strategies abstract class
class CookieTokenAuthStrategy(AuthStrategy):
    def authenticate(self, request, data):
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            logger.info("Login attempt for username: %s", username)
            user = authenticate(request, username=username, password=password)
            if user:
                return user, None
            logger.warning("Invalid credentials for username: %s", username)
            return None, {"non_field_errors": ["Invalid credentials"]}
        logger.warning("Login serializer errors: %s", serializer.errors)
        return None, serializer.errors

    def generate_token(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        return token.key

    

#! strategy pattern engine 

class AuthService:
    def __init__(self, strategy=CookieTokenAuthStrategy()):
        self.strategy = strategy

    def signup(self, request):
        logger.info("Signup request received with data: %s", request.data)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info("User created successfully: %s (ID: %s)", user.username, user.id)
            user_signed_up.send(sender=self.__class__, user=user)  # Preserve signal
            token = self.strategy.generate_token(user)
            if request.accepted_renderer.format == 'html':
                login(request, user, backend='apps.accounts.backends.EmailOrUsernameBackend')
            return user, token, None
        logger.warning("Signup validation errors: %s", serializer.errors)
        return None, None, serializer.errors

    def login(self, request):
        user, errors = self.strategy.authenticate(request, request.data)
        if user:
            token = self.strategy.generate_token(user)
            if request.accepted_renderer.format == 'html':
                login(request, user, backend='apps.accounts.backends.EmailOrUsernameBackend')
            return user, token, None
        return None, None, errors