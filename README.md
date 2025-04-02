# Hyphen Toggle OpenFeature Provider

The **Hyphen Toggle OpenFeature Provider** is an OpenFeature provider implementation for the Hyphen Toggle platform in Python. It enables feature flag evaluation using the OpenFeature standard.

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Configuration Options](#configuration-options)
4. [Evaluation Context](#evaluation-context)
   - [HyphenUser](#hyphenuser)
   - [HyphenEvaluationContext](#hyphenevaluationcontext)
5. [License](#license)

---

## Getting Started

### Installation

Install the provider and the OpenFeature Python SDK:

```bash
pip install openfeature-sdk hyphen-openfeature-provider
```

## Quick Start

```python
from openfeature import api
from openfeature_provider_hyphen import (
    HyphenProvider,
    HyphenProviderOptions,
    HyphenEvaluationContext
)

# Initialize provider options
options = HyphenProviderOptions(
    application="your-app-name",
    environment="production"
)

# Create and set the provider
provider = HyphenProvider(
    public_key="your-public-key",
    options=options
)
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

# Create an evaluation context with all available options
context = HyphenEvaluationContext(
    targeting_key="user-123",
    attributes={
        "user": user,
        "ip_address": "192.168.1.1",
        "custom_attributes": {
            "device": "mobile",
            "platform": "ios"
        }
    }
)

# Evaluate different types of flags
try:
    # Boolean flag
    show_feature = client.get_boolean_value(
        flag_key="show-new-feature",
        default_value=False,
        evaluation_context=context
    )

    # String flag
    theme = client.get_string_value(
        flag_key="app-theme",
        default_value="light",
        evaluation_context=context
    )

    # Integer flag
    max_items = client.get_integer_value(
        flag_key="max-items",
        default_value=10,
        evaluation_context=context
    )

    # Object flag
    config = client.get_object_value(
        flag_key="feature-config",
        default_value={
            "enabled": True,
            "timeout": 30
        },
        evaluation_context=context
    )
except Exception as e:
    print(f"Error evaluating flags: {e}")
```

## Configuration Options

The `HyphenProviderOptions` class accepts the following parameters:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `application` | str | Yes | The application name or ID |
| `environment` | str | Yes | Environment identifier (can be environment ID or alternateId) |
| `horizon_urls` | List[str] | No | Custom Hyphen server URLs |
| `enable_toggle_usage` | bool | No | Enable/disable telemetry (default: True) |
| `cache_ttl_seconds` | int | No | Cache TTL in seconds |
| `generate_cache_key_fn` | Callable | No | Custom cache key generation function |

## Evaluation Context

### HyphenUser

The `HyphenUser` class contains user-specific information:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str | Yes | Unique user identifier |
| `email` | str | No | User's email address |
| `name` | str | No | User's name |
| `custom_attributes` | Dict[str, Any] | No | Additional user attributes |

### HyphenEvaluationContext

The `HyphenEvaluationContext` class wraps all evaluation context data:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `targeting_key` | str | Yes | Key for evaluation targeting |
| `attributes` | Dict | No | Contains user, IP address, and custom attributes |

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
