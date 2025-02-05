import base64
import re
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagEvaluationDetails

def to_camel_case(snake_str: str) -> str:
    """Convert snake_case string to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def prepare_evaluate_payload(context: Optional[EvaluationContext] = None) -> Dict[str, Any]:
    """Prepare payload for the evaluate endpoint.
    
    Args:
        context: The evaluation context to transform
        
    Returns:
        A dictionary ready to be sent to the evaluate endpoint
    """
    if context is None:
        return {}
        
    # Convert context to dict and handle attributes
    payload = context.__dict__.copy()
    if 'attributes' in payload and payload['attributes']:
        attributes = payload.pop('attributes')
        payload.update(attributes)
    payload.pop('attributes', None)
    
    # Convert keys to camelCase
    return transform_dict_keys(payload)

def prepare_telemetry_details(details: FlagEvaluationDetails, hints: dict) -> dict:
    """Prepare evaluation details for telemetry.
    
    Args:
        details: The flag evaluation details
        hints: Additional hints from the evaluation process
        
    Returns:
        A dictionary ready for telemetry submission
    """
    return {
        "key": details.flag_key,
        "type": hints.get("flag_type", "unknown"),
        "value": details.value,
        "reason": details.reason,
        "errorMessage": details.error_message
    }

def transform_dict_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively transform all dictionary keys from snake_case to camelCase."""
    new_dict = {}
    for key, value in d.items():
        new_key = to_camel_case(key)
        if isinstance(value, dict):
            value = transform_dict_keys(value)
        elif isinstance(value, list):
            value = [transform_dict_keys(item) if isinstance(item, dict) else item for item in value]
        new_dict[new_key] = value
    return new_dict

def get_org_id_from_public_key(public_key: str) -> str:
    """Extract organization ID from public key."""
    try:
        key_without_prefix = public_key.replace('public_', '', 1)
        # Decode base64 directly
        decoded = base64.b64decode(key_without_prefix).decode('utf-8')
        org_id = decoded.split(':')[0]
        if re.match(r'^[a-zA-Z0-9_-]+$', org_id):
            return org_id
    except Exception:
        pass
    return ''

def build_default_horizon_url(public_key: str) -> str:
    """Build the default Horizon URL based on public key."""
    org_id = get_org_id_from_public_key(public_key)
    if org_id:
        return f'https://{org_id}.toggle.hyphen.cloud'
    return 'https://toggle.hyphen.cloud'

def build_url(base_url: str, path: str) -> str:
    """Build a complete URL by combining base URL and path."""
    parsed = urlparse(base_url)
    base_path = parsed.path.rstrip('/')
    clean_path = path.lstrip('/')
    
    if base_path:
        full_path = f"{base_path}/{clean_path}"
    else:
        full_path = clean_path
        
    # Reconstruct URL with new path
    parsed = parsed._replace(path=full_path)
    return parsed.geturl()
