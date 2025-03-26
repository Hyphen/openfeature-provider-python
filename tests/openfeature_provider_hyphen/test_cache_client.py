from openfeature_provider_hyphen.cache_client import CacheClient
from openfeature_provider_hyphen.types import HyphenEvaluationContext


def test_cache_operations():
    client = CacheClient()

    # Test with simple context
    context = HyphenEvaluationContext(targeting_key="user1")
    value = "test-value"

    # Initially should be None
    assert client.get(context) is None

    # Set and verify
    client.set(context, value)
    assert client.get(context) == value


def test_cache_key_generation():
    client = CacheClient()

    # Test with minimal context
    context1 = HyphenEvaluationContext(targeting_key="user1")
    key1 = client._default_generate_cache_key(context1)
    assert isinstance(key1, str)
    assert len(key1) > 0

    # Test with attributes
    context2 = HyphenEvaluationContext(
        targeting_key="user1", attributes={"custom_field": "value"}
    )
    key2 = client._default_generate_cache_key(context2)
    assert isinstance(key2, str)
    assert len(key2) > 0
    assert key1 != key2  # Different contexts should have different keys


def test_custom_key_generator():
    def custom_generator(context: HyphenEvaluationContext) -> str:
        return context.targeting_key

    client = CacheClient(generate_cache_key_fn=custom_generator)
    context = HyphenEvaluationContext(targeting_key="user1")
    value = "test-value"

    client.set(context, value)
    assert client.get(context) == value
    assert client.generate_cache_key_fn(context) == "user1"


def test_ttl():
    client = CacheClient(ttl_seconds=0)  # Immediate expiration
    context = HyphenEvaluationContext(targeting_key="user1")
    value = "test-value"

    client.set(context, value)
    assert client.get(context) is None  # Should expire immediately
