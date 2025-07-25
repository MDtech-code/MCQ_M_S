
from rest_framework.authtoken.models import Token
from django_redis import get_redis_connection

import logging

logger = logging.getLogger(__name__)



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