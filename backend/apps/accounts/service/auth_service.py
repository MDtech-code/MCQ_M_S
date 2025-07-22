
# accounts/services/auth_service.py
from abc import ABC, abstractmethod
from django.forms import ValidationError
from rest_framework.authtoken.models import Token
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer, UserLoginSerializer
from apps.accounts.signals import user_signed_up
from .security_service import SecurityService
from django.contrib.auth import authenticate, login
from django_redis import get_redis_connection
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class AuthStrategy(ABC):
    @abstractmethod
    def authenticate(self, request, data):
        pass

    @abstractmethod
    def generate_token(self, user):
        pass
# accounts/services.py
def get_or_create_token(user):
    # First ensure token exists in database (source of truth)
    token, created = Token.objects.get_or_create(user=user)
    
    cache_key = f"token:user:{user.id}"
    redis = get_redis_connection('default')
    
    # Check if cache needs update
    cached_token = redis.get(cache_key)
    needs_cache_update = not cached_token or cached_token.decode() != token.key
    
    if needs_cache_update:
        redis.setex(cache_key, 86400, token.key)  # Cache for 24 hours
        logger.info("Token cache updated for user %s", user.username)
    else:
        logger.debug("Token cache already current for user %s", user.username)
    
    logger.info("Token for user %s %s. %s",
               user.username, 
               "created" if created else "exists in database",
               "Cache updated" if needs_cache_update else "Cache current")
    
    return token.key, created

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

class AuthService:
    def __init__(self, strategy=CookieTokenAuthStrategy()):
        self.strategy = strategy

    @transaction.atomic
    def signup(self, request):
        logger.info("Signup request received with data: %s", request.data)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info("User created successfully: %s (ID: %s)", user.username, user.id)
            user_signed_up.send(sender=self.__class__, user=user)
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
    


# # accounts/services.py (replace CookieTokenAuthStrategy and add get_or_create_token)
# from abc import ABC, abstractmethod
# from rest_framework.authtoken.models import Token
# from apps.accounts.models import User
# from apps.accounts.serializers import UserSerializer, UserLoginSerializer
# from apps.accounts.signals import user_signed_up
# from django.contrib.auth import authenticate, login
# from django_redis import get_redis_connection
# import logging

# logger = logging.getLogger(__name__)

# class AuthStrategy(ABC):
#     @abstractmethod
#     def authenticate(self, request, data):
#         pass

#     @abstractmethod
#     def generate_token(self, user):
#         pass


# # accounts/services.py
# def get_or_create_token(user):
#     # First ensure token exists in database (source of truth)
#     token, created = Token.objects.get_or_create(user=user)
    
#     cache_key = f"token:user:{user.id}"
#     redis = get_redis_connection('default')
    
#     # Check if cache needs update
#     cached_token = redis.get(cache_key)
#     needs_cache_update = not cached_token or cached_token.decode() != token.key
    
#     if needs_cache_update:
#         redis.setex(cache_key, 86400, token.key)  # Cache for 24 hours
#         logger.info("Token cache updated for user %s", user.username)
#     else:
#         logger.debug("Token cache already current for user %s", user.username)
    
#     logger.info("Token for user %s %s. %s",
#                user.username, 
#                "created" if created else "exists in database",
#                "Cache updated" if needs_cache_update else "Cache current")
    
#     return token.key, created

# # def get_or_create_token(user):
    
# #     token, created = Token.objects.get_or_create(user=user)
# #     cache_key = f"token:user:{user.id}"
# #     redis = get_redis_connection('default')
# #     token_key = redis.get(cache_key)
# #     if token_key:
# #         logger.info("Token for user %s found in cache.", user.username)
# #         return token_key.decode(), False
# #     redis.setex(cache_key, 86400, token.key)  # Cache for 24 hours
# #     logger.info("Token for user %s %s in database.", user.username, "created" if created else "retrieved")
# #     return token.key, created

# class CookieTokenAuthStrategy(AuthStrategy):
#     def authenticate(self, request, data):
#         serializer = UserLoginSerializer(data=data)
#         if serializer.is_valid():
#             username = serializer.validated_data['username']
#             password = serializer.validated_data['password']
#             logger.info("Login attempt for username: %s", username)
#             user = authenticate(request, username=username, password=password)
#             if user:
#                 return user, None
#             logger.warning("Invalid credentials for username: %s", username)
#             return None, {"non_field_errors": ["Invalid credentials"]}
#         logger.warning("Login serializer errors: %s", serializer.errors)
#         return None, serializer.errors

#     def generate_token(self, user):
#         token, _ = get_or_create_token(user)
#         return token

# class AuthService:
#     def __init__(self, strategy=CookieTokenAuthStrategy()):
#         self.strategy = strategy

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

# accounts/services.py
# from abc import ABC, abstractmethod
# from rest_framework.authtoken.models import Token
# from apps.accounts.models import User
# from apps.accounts.serializers import UserSerializer, UserLoginSerializer
# from apps.accounts.signals import user_signed_up
# from django.contrib.auth import authenticate, login
# import logging


# logger = logging.getLogger(__name__)


# #! abstract class Strategies
# class AuthStrategy(ABC):
#     @abstractmethod
#     def authenticate(self, request, data):
#         pass

#     @abstractmethod
#     def generate_token(self, user):
#         pass


# #! concrete implementation of strategies abstract class
# class CookieTokenAuthStrategy(AuthStrategy):
#     def authenticate(self, request, data):
#         serializer = UserLoginSerializer(data=data)
#         if serializer.is_valid():
#             username = serializer.validated_data['username']
#             password = serializer.validated_data['password']
#             logger.info("Login attempt for username: %s", username)
#             user = authenticate(request, username=username, password=password)
#             if user:
#                 return user, None
#             logger.warning("Invalid credentials for username: %s", username)
#             return None, {"non_field_errors": ["Invalid credentials"]}
#         logger.warning("Login serializer errors: %s", serializer.errors)
#         return None, serializer.errors

#     def generate_token(self, user):
#         token, _ = Token.objects.get_or_create(user=user)
#         return token.key

    

# #! strategy pattern engine 

# class AuthService:
#     def __init__(self, strategy=CookieTokenAuthStrategy()):
#         self.strategy = strategy

#     def signup(self, request):
#         logger.info("Signup request received with data: %s", request.data)
#         serializer = UserSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             logger.info("User created successfully: %s (ID: %s)", user.username, user.id)
#             user_signed_up.send(sender=self.__class__, user=user)  # Preserve signal
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