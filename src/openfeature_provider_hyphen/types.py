from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from openfeature.flag_evaluation import Reason

@dataclass
class HyphenProviderOptions:
    """Options for configuring the Hyphen provider."""
    application: str
    environment: str
    horizon_urls: Optional[List[str]] = None
    enable_toggle_usage: bool = True
    cache_ttl_seconds: Optional[int] = None

@dataclass
class HyphenUser:
    """User information for Hyphen evaluation context."""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None

@dataclass
class HyphenEvaluationContext:
    """Extended evaluation context for Hyphen provider."""
    targeting_key: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    user: Optional[HyphenUser] = None
    application: Optional[str] = None
    environment: Optional[str] = None

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
    data: Dict[str, Evaluation]  # {'toggle': Evaluation}
