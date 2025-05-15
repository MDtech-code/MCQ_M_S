from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class UserCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            cache_key = f"user:{request.user.id}"
            cached_user = cache.get(cache_key)
            if not cached_user:
                cache.set(cache_key, request.user, timeout=3600)  # 1 hour
                logger.debug(f"Cached user {request.user.id}")
        return self.get_response(request)