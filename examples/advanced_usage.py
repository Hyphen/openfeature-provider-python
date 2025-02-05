from openfeature import api
from openfeature_provider_hyphen import (
    HyphenProvider,
    HyphenProviderOptions,
    HyphenEvaluationContext,
    HyphenUser
)
from typing import Dict, Any

def custom_cache_key_generator(context: HyphenEvaluationContext) -> str:
    """Example of a custom cache key generator function."""
    # Combine targeting key with user ID if available
    if 'user' in context.attributes:
        user = context.attributes['user']
        if isinstance(user, HyphenUser):
            return f"{context.targeting_key}:{user.id}"
    return context.targeting_key

def main():
    # Initialize provider options with all available configurations
    options = HyphenProviderOptions(
        # Required options
        application="my-app",
        environment="development",
        
        # Optional configurations
        horizon_urls=["https://my-own-edge-server.com"],
        enable_toggle_usage=False,  # Disable telemetry
        cache_ttl_seconds=300,     # Cache TTL of 5 minutes
        generate_cache_key_fn=custom_cache_key_generator  # Custom cache key generation
    )

    # Create Hyphen provider instance
    provider = HyphenProvider(
        public_key="<YOUR-PUBLIC-KEY>",
        options=options
    )

    # Register the provider with OpenFeature
    api.set_provider(provider)

    # Create a client
    client = api.get_client()

    # Create a user with all available fields
    user = HyphenUser(
        id="user-123",
        email="user@example.com",
        name="John Doe",
        custom_attributes={
            "role": "admin",
            "subscription": "premium"
        }
    )

    # Create custom attributes
    custom_attributes: Dict[str, Any] = {
        "device": "mobile",
        "platform": "ios",
        "version": "2.0.0"
    }

    # Create an evaluation context with all available options
    context = HyphenEvaluationContext(
        targeting_key="user-123",
        attributes={
            "user": user,
            "ip_address": "192.168.1.1",
            "custom_attributes": custom_attributes
        }
    )

    # Evaluate different types of flags
    try:
        # Boolean flag evaluations
        show_feature = client.get_boolean_value(
            flag_key="show-new-feature",
            default_value=False,
            evaluation_context=context
        )
        print(f"Boolean flag 'show-new-feature': {show_feature}")

        # String flag evaluations
        theme = client.get_string_value(
            flag_key="app-theme",
            default_value="light",
            evaluation_context=context
        )
        print(f"String flag 'app-theme': {theme}")

        # Integer flag evaluations
        max_items = client.get_integer_value(
            flag_key="max-items",
            default_value=10,
            evaluation_context=context
        )
        print(f"Integer flag 'max-items': {max_items}")

        # Object flag evaluations
        config = client.get_object_value(
            flag_key="feature-config",
            default_value={
                "enabled": True,
                "timeout": 30,
                "retries": 3
            },
            evaluation_context=context
        )
        print(f"Object flag 'feature-config': {config}")

    except Exception as e:
        print(f"Error evaluating flags: {e}")

if __name__ == "__main__":
    main()
