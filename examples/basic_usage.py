from openfeature import api
from openfeature_provider_hyphen import HyphenProvider, HyphenProviderOptions, HyphenEvaluationContext

def main():
    # Initialize provider options
    options = HyphenProviderOptions(
        application="my-app",
        environment="development",
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

    # Create a simple evaluation context
    context = HyphenEvaluationContext(
        targeting_key="user-123"
    )

    # Evaluate different types of flags
    try:
        # Boolean flag evaluation
        show_feature = client.get_boolean_value(
            flag_key="show-new-feature",
            default_value=False,
            evaluation_context=context
        )
        print(f"Boolean flag 'show-new-feature': {show_feature}")

        # String flag evaluation
        theme = client.get_string_value(
            flag_key="app-theme",
            default_value="light",
            evaluation_context=context
        )
        print(f"String flag 'app-theme': {theme}")

        # Integer flag evaluation
        max_items = client.get_integer_value(
            flag_key="max-items",
            default_value=10,
            evaluation_context=context
        )
        print(f"Integer flag 'max-items': {max_items}")

        # Object flag evaluation
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
