import base64
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagEvaluationDetails
from openfeature_provider_hyphen.utils import (
    get_org_id_from_public_key, 
    build_default_horizon_url, 
    build_url,
    prepare_evaluate_payload,
    prepare_telemetry_details
)

def test_get_org_id_from_public_key():
    # Test valid public key
    # Create a base64 string that when decoded would be "test:key"
    test_key = base64.b64encode(b"test:key").decode('utf-8')
    public_key = "public_" + test_key
    organization_id = get_org_id_from_public_key(public_key)
    assert organization_id == "test"

    # Test invalid public key
    organization_id = get_org_id_from_public_key("invalid_key")
    assert organization_id == ""

def test_build_default_horizon_url():
    # Test with org ID
    test_key = base64.b64encode(b"test:key").decode('utf-8')
    public_key = "public_" + test_key
    url = build_default_horizon_url(public_key)
    assert url == "https://test.toggle.hyphen.cloud"

    # Test without org ID
    url = build_default_horizon_url("invalid_key")
    assert url == "https://toggle.hyphen.cloud"

def test_prepare_evaluate_payload():
    # Test with empty context
    assert prepare_evaluate_payload(None) == {}

    # Test with context and attributes
    context = EvaluationContext(
        targeting_key="test-key",
        attributes={"custom": "value"}
    )
    payload = prepare_evaluate_payload(context)
    assert payload["targetingKey"] == "test-key"
    assert payload["custom"] == "value"
    assert "attributes" not in payload

def test_prepare_telemetry_details():
    details = FlagEvaluationDetails(
        flag_key="test-flag",
        value=True,
        reason="test-reason",
        error_message="test-error"
    )
    hints = {"flag_type": "boolean"}
    
    result = prepare_telemetry_details(details, hints)
    assert result["key"] == "test-flag"
    assert result["type"] == "boolean"
    assert result["value"] is True
    assert result["reason"] == "test-reason"
    assert result["errorMessage"] == "test-error"

    # Test with missing flag_type
    result = prepare_telemetry_details(details, {})
    assert result["type"] == "unknown"

def test_build_url():
    # Test with base path
    url = build_url("https://example.com/base", "/path")
    assert url == "https://example.com/base/path"

    # Test without base path
    url = build_url("https://example.com", "/path")
    assert url == "https://example.com/path"

    # Test with trailing slash
    url = build_url("https://example.com/base/", "/path")
    assert url == "https://example.com/base/path"

    # Test with leading slash in path
    url = build_url("https://example.com/base", "path")
    assert url == "https://example.com/base/path"
