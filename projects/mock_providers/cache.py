from functools import wraps
from typing import Callable

from cachetools import TTLCache, keys

from .config import QUOTE_TTL


CACHES: dict[str, TTLCache] = {
    "a": TTLCache(maxsize=1024, ttl=QUOTE_TTL),
    "b": TTLCache(maxsize=1024, ttl=QUOTE_TTL),
    "c": TTLCache(maxsize=1024, ttl=QUOTE_TTL),
}


def async_cachedmethod(get_caches: Callable):
    def dec(method):
        @wraps(method)
        async def memoized_async_method(*args, **kwargs):
            caches_dict = get_caches()
            provider_id = kwargs.get("provider_id")

            if provider_id not in caches_dict:
                return await method(*args, **kwargs)

            cache = caches_dict[provider_id]
            key = keys.hashkey(*args, **kwargs)
            if key in cache:
                return cache[key]
            result = await method(*args, **kwargs)
            cache[key] = result
            return result

        return memoized_async_method

    return dec
