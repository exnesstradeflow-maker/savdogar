import time
import logging

logger = logging.getLogger(__name__)

_cache = {}

def cached(ttl: int = 60):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in _cache and now - _cache[key]["time"] < ttl:
                logger.debug(f"Cache hit: {func.__name__}")
                return _cache[key]["value"]
            result = await func(*args, **kwargs)
            _cache[key] = {"value": result, "time": now}
            return result
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

def clear_cache():
    _cache.clear()
    logger.info("Cache cleared")
