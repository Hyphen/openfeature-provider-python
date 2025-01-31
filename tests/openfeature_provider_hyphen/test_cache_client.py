import pytest
from openfeature_provider_hyphen.cache_client import CacheClient
from openfeature_provider_hyphen.types import HyphenEvaluationContext, HyphenUser

def test_cache_client_initialization():
    # Test default TTL
    client = CacheClient()
    assert client.cache.ttl == 30

    # Test custom TTL
    client = CacheClient(ttl_seconds=60)
    assert client.cache.ttl == 60

def test_cache_key_generation():
    client = CacheClient()
    
    # Test with minimal context
    context1 = HyphenEvaluationContext(targeting_key="user1")
    key1 = client._default_generate_cache_key(context1)
    assert isinstance(key1, str)
    assert len(key1) > 0

    # Test with full context
    context2 = HyphenEvaluationContext(
        targeting_key="user1",
        ip_address="127.0.0.1",
        custom_attributes={"attr1": "value1"},
        user=HyphenUser(
            id="user1",
            email="test@example.com",
            name="Test User",
            custom_attributes={"user_attr": "value"}
        )
    )
    key2 = client._default_generate_cache_key(context2)
    assert isinstance(key2, str)
    assert len(key2) > 0
    
    # Different contexts should generate different keys
    assert key1 != key2

def test_cache_operations():
    client = CacheClient(ttl_seconds=1)
    context = HyphenEvaluationContext(targeting_key="user1")
    test_value = {"flag": "value"}

    # Test set and get
    client.set(context, test_value)
    cached_value = client.get(context)
    assert cached_value == test_value

    # Test custom key generation function
    def custom_key_gen(ctx):
        return f"custom-{ctx.targeting_key}"

    client = CacheClient(ttl_seconds=1, generate_cache_key_fn=custom_key_gen)
    client.set(context, test_value)
    cached_value = client.get(context)
    assert cached_value == test_value

    # Verify key was generated using custom function
    key = client.generate_cache_key_fn(context)
    assert key == "custom-user1"

def test_cache_ttl():
    import time
    
    client = CacheClient(ttl_seconds=1)
    context = HyphenEvaluationContext(targeting_key="user1")
    test_value = {"flag": "value"}

    # Set value
    client.set(context, test_value)
    assert client.get(context) == test_value

    # Wait for TTL to expire
    time.sleep(1.1)
    assert client.get(context) is None
