import pytest
from unittest.mock import Mock, patch
import requests

from openfeature_provider_hyphen.hyphen_client import HyphenClient
from openfeature_provider_hyphen.types import (
    HyphenProviderOptions,
    HyphenEvaluationContext,
    Evaluation,
    EvaluationResponse,
    TelemetryPayload,
)

@pytest.fixture
def mock_response():
    mock = Mock()
    mock.json.return_value = {
        "toggles": {
            "test-flag": {
                "key": "test-flag",
                "value": True,
                "type": "boolean",
                "reason": "STATIC",
            }
        }
    }
    mock.raise_for_status = Mock()
    return mock

@pytest.fixture
def client():
    options = HyphenProviderOptions(
        application="test-app",
        environment="test",
        horizon_urls=["https://test.example.com"]
    )
    return HyphenClient("test-key", options)

def test_client_initialization_with_custom_cache_key_fn():
    def custom_cache_key_fn(context: HyphenEvaluationContext) -> str:
        return f"custom-{context.targeting_key}"
        
    options = HyphenProviderOptions(
        application="test-app",
        environment="test",
        horizon_urls=["https://custom.example.com"],
        generate_cache_key_fn=custom_cache_key_fn
    )
    client = HyphenClient("test-key", options)
    
    # Test that the custom function was properly passed to CacheClient
    context = HyphenEvaluationContext(targeting_key="user1")
    assert client.cache.generate_cache_key_fn(context) == "custom-user1"

def test_client_initialization():
    options = HyphenProviderOptions(
        application="test-app",
        environment="test",
        horizon_urls=["https://custom.example.com"]
    )
    client = HyphenClient("test-key", options)
    
    assert client.public_key == "test-key"
    assert "https://custom.example.com" in client.horizon_urls
    assert client.default_horizon_url in client.horizon_urls
    assert client.session.headers["x-api-key"] == "test-key"
    assert client.session.headers["Content-Type"] == "application/json"

@patch("requests.Session.post")
def test_evaluate_success(mock_post, client, mock_response):
    mock_post.return_value = mock_response
    context = HyphenEvaluationContext(targeting_key="user1")

    response = client.evaluate(context)
    
    assert isinstance(response, EvaluationResponse)
    assert "test-flag" in response.toggles
    flag = response.toggles["test-flag"]
    assert isinstance(flag, Evaluation)
    assert flag.key == "test-flag"
    assert flag.value is True
    assert flag.type == "boolean"
    assert flag.reason == "STATIC"

    # Verify the request
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "toggle/evaluate" in args[0]
    assert kwargs["json"]["targetingKey"] == "user1"

@patch("requests.Session.post")
def test_evaluate_with_cache(mock_post, client, mock_response):
    mock_post.return_value = mock_response
    context = HyphenEvaluationContext(targeting_key="user1")
    
    # First call should hit the API
    response1 = client.evaluate(context)
    assert mock_post.call_count == 1
    
    # Second call should use cache
    response2 = client.evaluate(context)
    assert mock_post.call_count == 1  # Call count shouldn't increase
    
    assert response1.toggles == response2.toggles

@patch("requests.Session.post")
def test_evaluate_error_handling(mock_post, client):
    # Simulate network error
    mock_post.side_effect = requests.RequestException("Network error")
    context = HyphenEvaluationContext(targeting_key="user1")

    with pytest.raises(requests.RequestException) as exc_info:
        client.evaluate(context)
    assert "Network error" in str(exc_info.value)

@patch("requests.Session.post")
def test_post_telemetry(mock_post, client, mock_response):
    mock_post.return_value = mock_response
    
    # Create context dictionary directly
    context = {
        "targetingKey": "user1",
        "application": "test-app",
        "environment": "test"
    }
    
    # Create evaluation details dictionary directly
    evaluation = {
        "flagKey": "test-flag",
        "value": True,
        "reason": "STATIC",
        "variant": "control"
    }
    
    payload = TelemetryPayload(
        context=context,
        data={"toggle": evaluation}
    )

    # Should not raise any exceptions
    client.post_telemetry(payload)

    # Verify the request
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "toggle/telemetry" in args[0]
    
    # Verify context is properly transformed
    assert kwargs["json"]["context"]["targetingKey"] == "user1"
    assert kwargs["json"]["context"]["application"] == "test-app"
    assert kwargs["json"]["context"]["environment"] == "test"
    
    # Verify telemetry data is properly formatted
    toggle_data = kwargs["json"]["data"]["toggle"]
    assert toggle_data["flagKey"] == "test-flag"
    assert toggle_data["value"] is True
    assert toggle_data["reason"] == "STATIC"

@patch("requests.Session.post")
def test_try_urls_fallback(mock_post, client):
    # First URL fails, second succeeds
    mock_response = Mock()
    mock_response.json.return_value = {
        "toggles": {
            "test-flag": {
                "key": "test-flag",
                "value": True,
                "type": "boolean",
                "reason": "STATIC",
            }
        }
    }
    mock_response.raise_for_status = Mock()
    
    mock_post.side_effect = [
        requests.RequestException("First URL failed"),
        mock_response
    ]
    
    # Make a request to trigger URL fallback
    context = HyphenEvaluationContext(targeting_key="user1")
    response = client.evaluate(context)
    
    # Verify both URLs were tried
    assert mock_post.call_count == 2
    call_urls = [args[0] for args, _ in mock_post.call_args_list]
    assert len(call_urls) == 2
    assert "test.example.com" in call_urls[0]
    assert client.default_horizon_url in call_urls[1]
    
    # Verify we got the successful response
    assert isinstance(response, EvaluationResponse)
    assert "test-flag" in response.toggles

@patch("requests.Session.post")
def test_try_urls_all_fail(mock_post, client):
    # All URLs fail
    mock_post.side_effect = requests.RequestException("Network error")
    
    context = HyphenEvaluationContext(targeting_key="user1")
    
    with pytest.raises(requests.RequestException):
        client.evaluate(context)
    
    # Verify all URLs were tried
    assert mock_post.call_count == len(client.horizon_urls)
