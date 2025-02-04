import json
from typing import Any, Dict, List, Optional, Union

from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import (
    FlagResolutionDetails,
    FlagEvaluationDetails,
    Reason,
)
from openfeature.exception import (
    ErrorCode,
    FlagNotFoundError,
    GeneralError,
    TypeMismatchError,
)
from openfeature.hook import Hook, HookContext
from openfeature.provider import Metadata, AbstractProvider

from .types import HyphenEvaluationContext, HyphenProviderOptions, TelemetryPayload
from .hyphen_client import HyphenClient

class HyphenProvider(AbstractProvider):
    """OpenFeature provider implementation for Hyphen."""

    def __init__(self, public_key: str, options: HyphenProviderOptions):
        """Initialize the Hyphen provider.
        
        Args:
            public_key: The public API key for authentication
            options: Configuration options for the provider
        """
        if not options.application:
            raise ValueError("Application is required")
        if not options.environment:
            raise ValueError("Environment is required")

        self.options = options
        self.hyphen_client = HyphenClient(public_key, options)

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
        class TelemetryHook(Hook):
            def __init__(self, provider: 'HyphenProvider'):
                self.provider = provider

            def after(
                self,
                hook_context: HookContext,
                details: FlagEvaluationDetails,
            ) -> None:
                context = hook_context.context
                if not isinstance(context, HyphenEvaluationContext):
                    context = HyphenEvaluationContext(
                        targeting_key=context.targeting_key,
                        attributes=context.attributes
                    )

                payload = TelemetryPayload(
                    context=context,
                    data={'toggle': details}
                )

                try:
                    self.provider.hyphen_client.post_telemetry(payload)
                except Exception as error:
                    print("Unable to log usage", error)

        return TelemetryHook(self)

    def _get_targeting_key(self, context: EvaluationContext) -> str:
        """Get the targeting key from the context."""
        if isinstance(context, HyphenEvaluationContext):
            if context.targeting_key:
                return context.targeting_key
            if context.user and context.user.id:
                return context.user.id

        if context.targeting_key:
            return context.targeting_key

        # Generate a default targeting key
        return f"{self.options.application}-{self.options.environment}-{id(context)}"

    def _prepare_context(self, context: Optional[EvaluationContext] = None) -> HyphenEvaluationContext:
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
        default_value: Any
    ) -> FlagResolutionDetails:
        """Get flag evaluation from the client."""
        prepared_context = self._prepare_context(context)
        response = self.hyphen_client.evaluate(prepared_context)
        evaluation = response.toggles.get(flag_key)

        if evaluation is None:
            raise FlagNotFoundError('Flag not found')

        if evaluation.error_message:
            raise GeneralError(str(evaluation.error_message))
        
        if evaluation.type != expected_type:
            return self._wrong_type(default_value)

        return FlagResolutionDetails(
            value=evaluation.value,
            variant=str(evaluation.value),
            reason=evaluation.reason or Reason.TARGETING_MATCH
        )


    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        context: Optional[EvaluationContext] = None
    ) -> FlagResolutionDetails[bool]:
        """Resolve boolean flag values."""
        return self._get_evaluation(flag_key, context, "boolean", default_value)

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        context: Optional[EvaluationContext] = None
    ) -> FlagResolutionDetails[str]:
        """Resolve string flag values."""
        return self._get_evaluation(flag_key, context, "string", default_value)

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        context: Optional[EvaluationContext] = None
    ) -> FlagResolutionDetails[int]:
        """Resolve integer flag values."""
        details = self._get_evaluation(flag_key, context, "number", default_value)
        details.value = int(details.value)
        return details

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        context: Optional[EvaluationContext] = None
    ) -> FlagResolutionDetails[float]:
        """Resolve float flag values."""
        details = self._get_evaluation(flag_key, context, "number", default_value)
        details.value = float(details.value)
        return details

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: Union[Dict, List],
        context: Optional[EvaluationContext] = None
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
                error_code=ErrorCode.PARSE_ERROR
            )
