# Hyphen Toggle OpenFeature Provider

The **Hyphen Toggle OpenFeature Provider** is an OpenFeature provider implementation for the Hyphen Toggle platform in Python. It enables feature flag evaluation using the OpenFeature standard.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Usage](#usage)
3. [Configuration](#configuration)
4. [Contributing](#contributing)
5. [License](#license)

---

## Getting Started

### Installation

Install the provider and the OpenFeature Python SDK:

```bash
pip install openfeature-sdk hyphen-openfeature-provider
```

## Usage

### Example: Feature Flag Evaluation

To evaluate a feature flag with specific user or application context, define and pass an `EvaluationContext`:

```python
from openfeature_provider_hyphen import HyphenUser, HyphenEvaluationContext

# Create user details
user = HyphenUser(
    id="user-123",
    email="user@example.com",
    name="John Doe",
    custom_attributes={"role": "admin"}
)

# Create evaluation context
context = HyphenEvaluationContext(
    targeting_key="user-123",
    attributes={
        "user": user,
        "ip_address": "203.0.113.42",
        "custom_attributes": {
            "subscription_level": "premium",
            "region": "us-east"
        }
    }
)

# Evaluate the toggle with context
flag_details = await client.get_boolean_value(
    "toggle-key",
    default_value=False,
    evaluation_context=context
)

print(flag_details)  # True or False
```

## Configuration

### Options

| Option | Type | Description | Required |
|--------|------|-------------|----------|
| `application` | str | The application id or alternate id. | Yes |
| `environment` | str | The environment in which your application is running (e.g., `production`, `staging`). | Yes |
| `horizon_urls` | List[str] | A list of Hyphen Horizon URLs to use for fetching feature flags. | No |
| `enable_toggle_usage` | bool | Enable or disable the logging of toggle usage (telemetry). | No |
| `cache` | dict | Configuration for caching feature flag evaluations. | No |

### Cache Configuration

The `cache` option accepts the following properties:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ttl_seconds` | int | 300 | Time-to-live in seconds for cached flag evaluations. |
| `generate_cache_key_fn` | Callable | - | Custom function to generate cache keys from evaluation context. |

Example with cache configuration:

```python
options = HyphenProviderOptions(
    application="your-application-name",
    environment="production",
    cache={
        "ttl_seconds": 600,  # 10 minutes
        "generate_cache_key_fn": lambda context: f"{context['targeting_key']}-{context['user']['id']}"
    }
)

# Example using an project environment id
# options = HyphenProviderOptions(
#     application="your-application-name",
#     environment="pevr_abc123",
#     cache={
#         "ttl_seconds": 600,  # 10 minutes
#         "generate_cache_key_fn": lambda context: f"{context['targeting_key']}-{context['user']['id']}"
#     }
# )
```

### Context

The SDK provides two main classes for structuring evaluation context:

#### HyphenEvaluationContext

The main context class that wraps all evaluation context data.

| Field | Type | Description |
|-------|------|-------------|
| `targeting_key` | str | The key used for caching the evaluation response. |
| `attributes` | dict | Dictionary containing user details, IP address, and custom attributes. |

#### HyphenUser

Class for structuring user information within the context.

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | The unique identifier of the user. |
| `email` | str | (Optional) The email address of the user. |
| `name` | str | (Optional) The name of the user. |
| `custom_attributes` | dict | (Optional) Custom attributes specific to the user. |

The `attributes` dictionary in `HyphenEvaluationContext` can contain:
- `user`: Instance of `HyphenUser`
- `ip_address`: str - The IP address of the user making the request
- `custom_attributes`: dict - Additional contextual information

## Contributing

We welcome contributions to this project! If you'd like to contribute, please follow the guidelines outlined in CONTRIBUTING.md. Whether it's reporting issues, suggesting new features, or submitting pull requests, your help is greatly appreciated!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for full details.
