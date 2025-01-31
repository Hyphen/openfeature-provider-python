import pytest
from unittest.mock import Mock, patch
import logging
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import Reason

from openfeature_provider_hyphen.provider import HyphenProvider
from openfeature_provider_hyphen.types import (
    HyphenProviderOptions,
    HyphenEvaluationContext,
    HyphenUser,
    Evaluation,
    EvaluationResponse,
    TelemetryPayload,
)

@pytest.fixture
def provider():
    options = HyphenProviderOptions(
        application="test-app",
        environment="test"
    )
    return HyphenProvider("test-key", options)

@pytest.fixture
def mock_evaluation():
    return {
        "test-flag": Evaluation(
            key="test-flag",
            value=True,
            type="boolean",
            reason=Reason.STATIC
        )
    }

def test_provider_initialization():
    # Test with valid options
    options = HyphenProviderOptions(
        application="test-app",
        environment="test"
    )
    provider = HyphenProvider("test-key", options)
    assert provider.options == options
    
    # Test with missing application
    with pytest.raises(ValueError, match="Application is required"):
        HyphenProvider("test-key", HyphenProviderOptions(
            application="",
            environment="test"
        ))
    
    # Test with missing environment
    with pytest.raises(ValueError, match="Environment is required"):
        HyphenProvider("test-key", HyphenProviderOptions(
            application="test-app",
            environment=""
        ))

def test_get_metadata(provider):
    metadata = provider.get_metadata()
    assert metadata.name == "hyphen-toggle-python"

def test_get_provider_hooks(provider):
    # Test with telemetry enabled (default)
    hooks = provider.get_provider_hooks()
    assert len(hooks) == 1
    
    # Test with telemetry disabled
    provider.options.enable_toggle_usage = False
    hooks = provider.get_provider_hooks()
    assert len(hooks) == 0

def test_get_targeting_key(provider):
    # Test with HyphenEvaluationContext and targeting key
    context = HyphenEvaluationContext(targeting_key="user1")
    assert provider._get_targeting_key(context) == "user1"
    
    # Test with HyphenEvaluationContext and user ID
    context = HyphenEvaluationContext(
        targeting_key="",
        user=HyphenUser(id="user1")
    )
    assert provider._get_targeting_key(context) == "user1"
    
    # Test with standard EvaluationContext
    context = EvaluationContext(targeting_key="user1")
    assert provider._get_targeting_key(context) == "user1"
    
    # Test with no targeting key (should generate one)
    context = EvaluationContext()
    key = provider._get_targeting_key(context)
    assert provider.options.application in key
    assert provider.options.environment in key

def test_prepare_context(provider):
    # Test with no context
    context = provider._prepare_context()
    assert isinstance(context, HyphenEvaluationContext)
    assert context.application == provider.options.application
    assert context.environment == provider.options.environment
    
    # Test with standard EvaluationContext
    base_context = EvaluationContext(targeting_key="user1")
    context = provider._prepare_context(base_context)
    assert isinstance(context, HyphenEvaluationContext)
    assert context.targeting_key == "user1"
    assert context.application == provider.options.application
    assert context.environment == provider.options.environment
    
    # Test with HyphenEvaluationContext
    base_context = HyphenEvaluationContext(
        targeting_key="user1",
        ip_address="127.0.0.1"
    )
    context = provider._prepare_context(base_context)
    assert context.ip_address == "127.0.0.1"
    assert context.application == provider.options.application
    assert context.environment == provider.options.environment

@patch("openfeature_provider_hyphen.hyphen_client.HyphenClient.evaluate")
def test_resolve_boolean_details(mock_evaluate, provider, mock_evaluation):
    mock_evaluate.return_value = EvaluationResponse(toggles=mock_evaluation)
    logger = logging.getLogger()
    
    # Test successful evaluation
    result = provider.resolve_boolean_details("test-flag", False, None, logger)
    assert result.value is True
    assert result.reason == Reason.STATIC
    
    # Test wrong type
    mock_evaluation["test-flag"].type = "string"
    result = provider.resolve_boolean_details("test-flag", False, None, logger)
    assert result.value is False
    assert result.reason == Reason.ERROR
    
    # Test missing flag
    mock_evaluation.clear()
    result = provider.resolve_boolean_details("test-flag", False, None, logger)
    assert result.value is False
    assert result.reason == Reason.ERROR

@patch("openfeature_provider_hyphen.hyphen_client.HyphenClient.evaluate")
def test_resolve_string_details(mock_evaluate, provider):
    mock_evaluate.return_value = EvaluationResponse(toggles={
        "test-flag": Evaluation(
            key="test-flag",
            value="test-value",
            type="string",
            reason=Reason.STATIC
        )
    })
    logger = logging.getLogger()
    
    result = provider.resolve_string_details("test-flag", "default", None, logger)
    assert result.value == "test-value"
    assert result.reason == Reason.STATIC

@patch("openfeature_provider_hyphen.hyphen_client.HyphenClient.evaluate")
def test_resolve_number_details(mock_evaluate, provider):
    mock_evaluate.return_value = EvaluationResponse(toggles={
        "test-flag": Evaluation(
            key="test-flag",
            value=42,
            type="number",
            reason=Reason.STATIC
        )
    })
    logger = logging.getLogger()
    
    # Test integer
    result = provider.resolve_integer_details("test-flag", 0, None, logger)
    assert result.value == 42
    assert result.reason == Reason.STATIC
    
    # Test float
    result = provider.resolve_float_details("test-flag", 0.0, None, logger)
    assert result.value == 42.0
    assert result.reason == Reason.STATIC

@patch("openfeature_provider_hyphen.hyphen_client.HyphenClient.evaluate")
def test_resolve_object_details(mock_evaluate, provider):
    test_obj = {"key": "value"}
    mock_evaluate.return_value = EvaluationResponse(toggles={
        "test-flag": Evaluation(
            key="test-flag",
            value=test_obj,
            type="object",
            reason=Reason.STATIC
        )
    })
    logger = logging.getLogger()
    
    result = provider.resolve_object_details("test-flag", {}, None, logger)
    assert result.value == test_obj
    assert result.reason == Reason.STATIC

def test_telemetry_hook(provider):
    hook = provider._create_telemetry_hook()
    
    # Create mock context and details
    context = Mock()
    context.context = HyphenEvaluationContext(targeting_key="user1")
    context.flag_value_type = "boolean"
    
    details = Mock()
    details.flag_key = "test-flag"
    details.value = True
    details.reason = Reason.STATIC
    
    # Test hook execution
    with patch("openfeature_provider_hyphen.hyphen_client.HyphenClient.post_telemetry") as mock_post:
        hook.after(context, details, {})
        mock_post.assert_called_once()
        
        # Verify payload
        args = mock_post.call_args
        payload = args[0][0]
        assert isinstance(payload, TelemetryPayload)
        assert payload.context.targeting_key == "user1"
        assert payload.data["toggle"].key == "test-flag"
        assert payload.data["toggle"].value is True
