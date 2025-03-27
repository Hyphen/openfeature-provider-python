import json
import re
from typing import Any, Dict, List, Optional, Union

from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import (ErrorCode, FlagNotFoundError, GeneralError,
                                   TypeMismatchError)
from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.hook import Hook
from openfeature.provider import AbstractProvider, Metadata

from .hooks import TelemetryHook
from .hyphen_client import HyphenClient
from .types import HyphenEvaluationContext, HyphenProviderOptions


class HyphenProvider(AbstractProvider):
    """OpenFeature provider implementation for Hyphen."""

    def __init__(self, public_key: str, options: HyphenProviderOptions):
        """Initialize the Hyphen provider.

        Args:
            public_key: The public API key for authentication
            options: Configuration options for the provider
        """
        self._validate_options(options)

        self.options = options
        self.hyphen_client = HyphenClient(public_key, options)

    def _validate_options(self, options: HyphenProviderOptions):
        """Validate the provider options."""
        if not options.application:
            raise ValueError("Application is required")
        if not options.environment:
            raise ValueError("Environment is required")

        self._validate_environment_format(options.environment)

    def _validate_environment_format(self, environment: str):
        """Validate the environment identifier format."""
        is_environment_id = environment.startswith("pevr_")
        is_valid_alternate_id = bool(
            re.match(r"^(?!.*environments)[a-z0-9\-_]{1,25}$", environment)
        )

        if not (is_environment_id or is_valid_alternate_id):
            raise ValueError(
                'Invalid environment format. Must be either a project environment ID (starting with "pevr_") '
                "or a valid alternateId (1-25 characters, lowercase letters, numbers, hyphens, and underscores, "
                'and not containing the word "environments").'
            )

    def get_metadata(self) -> Metadata:
        """Get provider metadata."""
        return Metadata(name="hyphen-toggle-python")

    def get_provider_hooks(self) -> List[Hook]:
        """Get provider-specific hooks."""
        hooks = []

        if self.options.enable_toggle_usage:
            hooks.append(self._create_telemetry_hook())

        return hooks

    def _create_telemetry_hook(self) -> Hook:
        """Create a hook for telemetry tracking."""
        return TelemetryHook(self)

    def _get_targeting_key(self, context: EvaluationContext) -> str:
        """Get the targeting key from the context."""
        if isinstance(context, EvaluationContext):
            if context.targeting_key:
                return context.targeting_key
            if context.user and context.user.id:
                return context.user.id

        if context.targeting_key:
            return context.targeting_key

        # Generate a default targeting key
        return f"{self.options.application}-{self.options.environment}-{id(context)}"

    def _prepare_context(
        self, context: Optional[EvaluationContext] = None
    ) -> HyphenEvaluationContext:
        """Prepare the evaluation context."""
        if context is None:
            context = EvaluationContext()

        targeting_key = self._get_targeting_key(context)

        # Update existing HyphenEvaluationContext
        context.targeting_key = targeting_key
        context.application = self.options.application
        context.environment = self.options.environment
        return context

    def _wrong_type(self, value: Any) -> FlagResolutionDetails:
        """Create an error resolution for wrong type."""
        raise TypeMismatchError()

    def _get_evaluation(
        self,
        flag_key: str,
        context: Optional[EvaluationContext],
        expected_type: str,
        default_value: Any,
    ) -> FlagResolutionDetails:
        """Get flag evaluation from the client."""
        prepared_context = self._prepare_context(context)
        response = self.hyphen_client.evaluate(prepared_context)
        evaluation = response.toggles.get(flag_key)

        if evaluation is None:
            raise FlagNotFoundError("Flag not found")

        if evaluation.error_message:
            raise GeneralError(str(evaluation.error_message))

        if evaluation.type != expected_type:
            return self._wrong_type(default_value)

        return FlagResolutionDetails(
            value=evaluation.value,
            variant=str(evaluation.value),
            reason=evaluation.reason or Reason.TARGETING_MATCH,
            flag_metadata={"type": evaluation.type},
        )

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        """Resolve boolean flag values."""
        evaluation = self._get_evaluation(flag_key, context, "boolean", default_value)

        # Handle the value based on its type
        if isinstance(evaluation.value, bool):
            value = evaluation.value
        elif isinstance(evaluation.value, str):
            value = evaluation.value.lower() == "true"
        else:
            value = bool(evaluation.value)

        return FlagResolutionDetails(
            value=value,
            variant=str(value),
            reason=Reason.TARGETING_MATCH,
            flag_metadata={"type": "boolean"},
        )

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        """Resolve string flag values."""
        return self._get_evaluation(flag_key, context, "string", default_value)

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        """Resolve integer flag values."""
        details = self._get_evaluation(flag_key, context, "number", default_value)
        details.value = int(details.value)
        return details

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        """Resolve float flag values."""

        details = self._get_evaluation(flag_key, context, "number", default_value)
        details.value = float(details.value)
        return details

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: Union[Dict, List],
        context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[Union[Dict, List]]:
        """Resolve object flag values."""
        details = self._get_evaluation(flag_key, context, "object", default_value)
        try:
            if isinstance(details.value, str):
                details.value = json.loads(details.value)
            return details
        except (json.JSONDecodeError, TypeError):
            return FlagResolutionDetails(
                value=default_value,
                variant=str(default_value),
                reason=Reason.ERROR,
                error_code=ErrorCode.PARSE_ERROR,
            )
