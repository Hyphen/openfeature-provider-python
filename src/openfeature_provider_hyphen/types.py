from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from openfeature.flag_evaluation import FlagEvaluationDetails, Reason


@dataclass
class HyphenProviderOptions:
    """Options for configuring the Hyphen provider."""

    application: str
    """The application name or ID for the current evaluation."""
    environment: str
    """
    The environment identifier for the Hyphen project.
    This can be either:
    - A project environment ID (e.g., `pevr_abc123`)
    - A valid alternateId (1-25 characters, lowercase letters, numbers, hyphens, and underscores)
    """
    horizon_urls: Optional[List[str]] = None
    """The Hyphen server URL"""
    enable_toggle_usage: bool = True
    """Flag to enable toggle usage"""
    cache_ttl_seconds: Optional[int] = None
    """The time-to-live (TTL) in seconds for the cache."""
    generate_cache_key_fn: Optional[Callable[["HyphenEvaluationContext"], str]] = None
    """Generate a cache key function for the evaluation context."""


@dataclass
class HyphenUser:
    """User information for Hyphen evaluation context."""

    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None


@dataclass
class HyphenEvaluationContext:
    """
    Extended evaluation context for Hyphen provider.
    - 'targeting_key': A string representing the targeting key
    - 'attributes': A dictionary of additional custom attributes
        - 'user': A dictionary with user details (id, email, name, custom_attributes)
        - 'ip_address': A string representing the user's IP address
        - 'custom_attributes': A dictionary of additional custom attributes

    """

    targeting_key: str
    attributes: Dict[
        str,
        Union[
            HyphenUser,  # user details
            str,  # ip_address
            Dict[str, Any],  # custom_attributes
        ],
    ] = field(default_factory=dict)


@dataclass
class Evaluation:
    """Represents a feature flag evaluation."""

    key: str
    value: Union[bool, str, int, float, Dict[str, Any], List[Any]]
    type: str  # 'boolean' | 'string' | 'number' | 'object'
    reason: Optional[Reason] = None
    error_message: Optional[str] = None
    variant: Optional[str] = None


@dataclass
class EvaluationResponse:
    """Response from the Hyphen evaluation API."""

    toggles: Dict[str, Evaluation]


@dataclass
class TelemetryPayload:
    """Payload for telemetry data."""

    context: HyphenEvaluationContext
    data: Dict[str, FlagEvaluationDetails]  # {'toggle': FlagEvaluationDetails}
