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
    """
    Extended evaluation context for Hyphen provider.
    
    The 'attributes' dictionary can contain:
    - 'user': A dictionary with user details (id, email, name, custom_attributes)
    - 'ip_address': A string representing the user's IP address
    - 'custom_attributes': A dictionary of additional custom attributes
    
    Example structure:
    attributes = {
        'user': {
            'id': 'user123',
            'email': 'user@example.com',
            'name': 'John Doe',
            'custom_attributes': {'plan': 'premium'}
        },
        'ip_address': '192.168.1.1',
        'custom_attributes': {'region': 'US'}
    }
    """
    targeting_key: str
    attributes: Dict[str, Union[
        HyphenUser,  # user details
        str,             # ip_address
        Dict[str, Any]   # custom_attributes
    ]] = field(default_factory=dict)

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
