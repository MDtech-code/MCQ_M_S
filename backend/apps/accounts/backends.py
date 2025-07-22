 #! both username and email

# accounts/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.functions import Lower
from django_redis import get_redis_connection
import logging

logger = logging.getLogger(__name__)

UserModel = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        username = username.lower().strip() 
        cache_key = f"user:auth:{username.lower()}"
        redis = get_redis_connection('default')
        user_id = redis.get(cache_key)
        
        if user_id:
            try:
                user = UserModel.objects.get(id=user_id.decode())
                logger.info("User %s found in cache.", user.username)
            except UserModel.DoesNotExist:
                logger.warning("Cached user ID %s not found in database.", user_id.decode())
                user = None
        else:
            credential_fields = {
                'username': Q(lower_username=username.lower()),
                'email': Q(lower_email=username.lower())
            }
            query = Q()
            for field, condition in credential_fields.items():
                query |= condition
            try:
                user = UserModel.objects.annotate(
                    lower_username=Lower('username'),
                    lower_email=Lower('email')
                ).get(query)
                redis.setex(cache_key, 3600, user.id)  # Cache for 1 hour
                logger.info("User %s cached successfully.", user.username)
            except UserModel.DoesNotExist:
                logger.warning("Authentication failed: user %s does not exist.", username)
                user = None

        if user and user.check_password(password):
            logger.info("User %s authenticated successfully.", user.username)
            return user
        if user:
            logger.warning("Authentication failed: invalid password for user %s.", username)
        return None 

# from django.contrib.auth import get_user_model
# from django.contrib.auth.backends import ModelBackend
# from django.db.models import Q
# from django.db.models.functions import Lower
# User = get_user_model()

# class EmailOrUsernameBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         try:
#             # Try to get the user by username or email (case-insensitive)
#             username = username.strip().lower()
#             user = User.objects.annotate(
#                 lower_email=Lower('email'),
#                 lower_username=Lower('username')
#             ).filter(Q(lower_email=username) | Q(lower_username=username)).first()
#         except User.DoesNotExist:
#             return None
#         except User.MultipleObjectsReturned:
#             # Handle the case where multiple users have the same email
#             return User.objects.filter(email__iexact=username).order_by('id').first()

#         if user is not None and user.check_password(password):
#             return user
#         return None