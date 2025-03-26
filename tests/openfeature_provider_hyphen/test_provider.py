from unittest.mock import Mock, patch

import pytest
from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import (FlagNotFoundError, GeneralError,
                                   TypeMismatchError)
from openfeature.flag_evaluation import FlagResolutionDetails, Reason

from openfeature_provider_hyphen.provider import HyphenProvider
from openfeature_provider_hyphen.types import (Evaluation, EvaluationResponse,
                                               HyphenEvaluationContext,
                                               HyphenProviderOptions,
                                               TelemetryPayload)


@pytest.fixture
def provider():
    options = HyphenProviderOptions(application="test-app", environment="test")
    return HyphenProvider("test-key", options)


@pytest.fixture
def mock_evaluation():
    return {
        "test-flag": Evaluation(
            key="test-flag", value=True, type="boolean", reason=Reason.TARGETING_MATCH
        )
    }


def test_provider_initialization():
    # Test with valid options
    options = HyphenProviderOptions(application="test-app", environment="test")
    provider = HyphenProvider("test-key", options)
    assert provider.options == options

    # Test with missing application
    with pytest.raises(ValueError, match="Application is required"):
        HyphenProvider(
            "test-key", HyphenProviderOptions(application="", environment="test")
        )

    # Test with missing environment
    with pytest.raises(ValueError, match="Environment is required"):
        HyphenProvider(
            "test-key", HyphenProviderOptions(application="test-app", environment="")
        )


def test_provider_initialization_environment_validation_regex():
    # Test with valid project environment ID
    options = HyphenProviderOptions(application="test-app", environment="pevr_abc123")
    provider = HyphenProvider("test-key", options)
    assert provider.options == options

    # Test with valid alternateId
    options = HyphenProviderOptions(application="test-app", environment="production")
    provider = HyphenProvider("test-key", options)
    assert provider.options == options

    # Test with invalid environment format (uppercase)
    with pytest.raises(ValueError, match="Invalid environment format"):
        HyphenProvider(
            "test-key",
            HyphenProviderOptions(application="test-app", environment="Production"),
        )

    # Test with invalid environment format (too long)
    with pytest.raises(ValueError, match="Invalid environment format"):
        HyphenProvider(
            "test-key",
            HyphenProviderOptions(
                application="test-app", environment="thisisaverylongenvironmentid"
            ),
        )

    # Test with invalid environment format (invalid characters)
    with pytest.raises(ValueError, match="Invalid environment format"):
        HyphenProvider(
            "test-key",
            HyphenProviderOptions(
                application="test-app", environment="test environment"
            ),
        )

    # Test with invalid environment format (contains "environments")
    with pytest.raises(ValueError, match="Invalid environment format"):
        HyphenProvider(
            "test-key",
            HyphenProviderOptions(
                application="test-app", environment="testenvironments"
            ),
        )


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
    # Test with targeting key
    context = HyphenEvaluationContext(targeting_key="user1")
    assert provider._get_targeting_key(context) == "user1"

    # Test with no targeting key (should generate one)
    context = HyphenEvaluationContext(targeting_key="")
    key = provider._get_targeting_key(context)
    assert provider.options.application in key
    assert provider.options.environment in key


def test_prepare_context(provider):
    # Test with no context
    context = provider._prepare_context(
        HyphenEvaluationContext(
            targeting_key="",
            attributes={
                "application": provider.options.application,
                "environment": provider.options.environment,
            },
        )
    )
    assert isinstance(context, HyphenEvaluationContext)
    assert provider.options.application in context.targeting_key
    assert provider.options.environment in context.targeting_key
    assert context.attributes["application"] == provider.options.application
    assert context.attributes["environment"] == provider.options.environment

    # Test with HyphenEvaluationContext
    base_context = HyphenEvaluationContext(
        targeting_key="user1",
        attributes={
            "application": provider.options.application,
            "environment": provider.options.environment,
        },
    )
    context = provider._prepare_context(base_context)
    assert isinstance(context, HyphenEvaluationContext)
    assert context.targeting_key == "user1"
    assert context.attributes["application"] == provider.options.application
    assert context.attributes["environment"] == provider.options.environment


@patch("openfeature_provider_hyphen.hyphen_client.HyphenClient.evaluate")
def test_resolve_boolean_details(mock_evaluate, provider, mock_evaluation):
    mock_evaluate.return_value = EvaluationResponse(toggles=mock_evaluation)

    # Test successful evaluation
    mock_evaluation["test-flag"] = Evaluation(
        key="test-flag",
        value="true",
        type="boolean",
        reason=Reason.TARGETING_MATCH,
    )
    mock_evaluate.return_value = EvaluationResponse(toggles=mock_evaluation)
    result = provider.resolve_boolean_details(
        "test-flag", False, HyphenEvaluationContext(targeting_key="user1")
    )
    assert result.value is True
    assert result.reason == Reason.TARGETING_MATCH

    # Test wrong type
    mock_evaluation["test-flag"] = Evaluation(
        key="test-flag", value="test", type="string", reason=Reason.TARGETING_MATCH
    )
    mock_evaluate.return_value = EvaluationResponse(toggles=mock_evaluation)
    with pytest.raises(TypeMismatchError):
        provider.resolve_boolean_details(
            "test-flag", False, HyphenEvaluationContext(targeting_key="user1")
        )

    # Test missing flag
    mock_evaluation.clear()
    mock_evaluate.return_value = EvaluationResponse(toggles=mock_evaluation)
    with pytest.raises(FlagNotFoundError):
        provider.resolve_boolean_details(
            "test-flag", False, HyphenEvaluationContext(targeting_key="user1")
        )

    # Test error message in evaluation
    mock_evaluation["test-flag"] = Evaluation(
        key="test-flag", value="true", type="boolean", error_message="Test error"
    )
    mock_evaluate.return_value = EvaluationResponse(toggles=mock_evaluation)
    with pytest.raises(GeneralError):
        provider.resolve_boolean_details(
            "test-flag", False, HyphenEvaluationContext(targeting_key="user1")
        )


@patch("openfeature_provider_hyphen.hyphen_client.HyphenClient.evaluate")
def test_resolve_string_details(mock_evaluate, provider):
    mock_evaluate.return_value = EvaluationResponse(
        toggles={
            "test-flag": Evaluation(
                key="test-flag",
                value="test-value",
                type="string",
                reason=Reason.TARGETING_MATCH,
            )
        }
    )

    result = provider.resolve_string_details(
        "test-flag", "default", HyphenEvaluationContext(targeting_key="user1")
    )
    assert result.value == "test-value"
    assert result.reason == Reason.TARGETING_MATCH


@patch("openfeature_provider_hyphen.hyphen_client.HyphenClient.evaluate")
def test_resolve_number_details(mock_evaluate, provider):
    mock_evaluate.return_value = EvaluationResponse(
        toggles={
            "test-flag": Evaluation(
                key="test-flag", value=42, type="number", reason=Reason.TARGETING_MATCH
            )
        }
    )

    # Test integer
    result = provider.resolve_integer_details(
        "test-flag", 0, HyphenEvaluationContext(targeting_key="user1")
    )
    assert result.value == 42
    assert result.reason == Reason.TARGETING_MATCH

    # Test float
    result = provider.resolve_float_details(
        "test-flag", 0.0, HyphenEvaluationContext(targeting_key="user1")
    )
    assert result.value == 42.0
    assert result.reason == Reason.TARGETING_MATCH


@patch("openfeature_provider_hyphen.hyphen_client.HyphenClient.evaluate")
def test_resolve_object_details(mock_evaluate, provider):
    test_obj = {"key": "value"}

    # Test with dict object
    mock_evaluate.return_value = EvaluationResponse(
        toggles={
            "test-flag": Evaluation(
                key="test-flag",
                value=test_obj,
                type="object",
                reason=Reason.TARGETING_MATCH,
            )
        }
    )

    result = provider.resolve_object_details(
        "test-flag", {}, HyphenEvaluationContext(targeting_key="user1")
    )
    assert result.value == test_obj
    assert result.reason == Reason.TARGETING_MATCH

    # Test with JSON string
    mock_evaluate.return_value = EvaluationResponse(
        toggles={
            "test-flag": Evaluation(
                key="test-flag",
                value='{"key": "value"}',
                type="object",
                reason=Reason.TARGETING_MATCH,
            )
        }
    )

    result = provider.resolve_object_details(
        "test-flag", {}, HyphenEvaluationContext(targeting_key="user1")
    )
    assert result.value == test_obj
    assert result.reason == Reason.TARGETING_MATCH


def test_telemetry_hook(provider):
    hook = provider._create_telemetry_hook()

    # Create mock context and details
    context = EvaluationContext(targeting_key="user1")

    details = FlagResolutionDetails(
        value=True,
        variant="true",
        reason=Reason.TARGETING_MATCH,
        flag_metadata={"type": "boolean"},
    )
    details.flag_key = "test-flag"  # Set flag_key after initialization

    hook_context = Mock()
    hook_context.evaluation_context = context
    hints = {"flag_type": "boolean"}

    # Test hook execution
    with patch(
        "openfeature_provider_hyphen.hyphen_client.HyphenClient.post_telemetry"
    ) as mock_post:
        hook.after(hook_context, details, hints)
        mock_post.assert_called_once()

        # Verify payload
        args = mock_post.call_args
        payload = args[0][0]
        assert isinstance(payload, TelemetryPayload)

        # Verify context transformation
        assert payload.context["targetingKey"] == "user1"
        assert payload.context["application"] == provider.options.application
        assert payload.context["environment"] == provider.options.environment

        # Verify telemetry details
        toggle_data = payload.data["toggle"]
        assert toggle_data["key"] == "test-flag"
        assert toggle_data["type"] == "boolean"
        assert toggle_data["value"] is True
        assert toggle_data["reason"] == Reason.TARGETING_MATCH
