import hashlib
import json
from dataclasses import asdict
from typing import Callable, Optional, TypeVar

from cachetools import TTLCache

from .types import HyphenEvaluationContext

T = TypeVar("T")


class CacheClient:
    """Client for caching feature flag evaluations."""

    def __init__(
        self,
        ttl_seconds: int = 30,
        generate_cache_key_fn: Optional[
            Callable[[HyphenEvaluationContext], str]
        ] = None,
    ):
        """Initialize the cache client.

        Args:
            ttl_seconds: Time-to-live in seconds for cache entries
            generate_cache_key_fn: Optional function to generate cache keys
        """
        self.cache = TTLCache(maxsize=100, ttl=ttl_seconds)
        self.generate_cache_key_fn = (
            generate_cache_key_fn or self._default_generate_cache_key
        )

    def _default_generate_cache_key(self, context: HyphenEvaluationContext) -> str:
        """Generate a default cache key from the evaluation context.

        Args:
            context: The evaluation context to generate a key for

        Returns:
            A string hash of the context
        """
        # Convert context to a dictionary, excluding None values
        context_dict = {
            k: (asdict(v) if hasattr(v, "__dataclass_fields__") else v)
            for k, v in context.__dict__.items()
            if v is not None
        }

        # Sort dictionary to ensure consistent ordering
        context_str = json.dumps(context_dict, sort_keys=True)

        # Generate SHA-256 hash
        return hashlib.sha256(context_str.encode()).hexdigest()

    def get(self, context: HyphenEvaluationContext) -> Optional[T]:
        """Get a value from the cache.

        Args:
            context: The evaluation context to get the cached value for

        Returns:
            The cached value if found, None otherwise
        """
        key = self.generate_cache_key_fn(context)
        return self.cache.get(key)

    def set(self, context: HyphenEvaluationContext, value: T) -> None:
        """Set a value in the cache.

        Args:
            context: The evaluation context to set the cached value for
            value: The value to cache
        """
        key = self.generate_cache_key_fn(context)
        self.cache[key] = value
