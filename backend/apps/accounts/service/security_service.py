# accounts/services/security_service.py
from django_redis import get_redis_connection
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class SecurityService:
    @staticmethod
    def limit_login_attempts(username):
        cache_key = f"login_attempts:{username.lower()}"
        redis = get_redis_connection('default')
        attempts = redis.get(cache_key)
        attempts = int(attempts) if attempts else 0
        
        if attempts >= 5:
            logger.warning("Rate limit exceeded for username: %s", username)
            raise ValidationError("Too many login attempts. Please try again in 5 minutes.")
        
        attempts += 1
        redis.setex(cache_key, 300, attempts)  # 5-minute window
        logger.info("Login attempt %d for username: %s", attempts, username)
        return True