import logging
from typing import Any, Dict, List, Optional, Union

from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import (
    FlagResolutionDetails,
    FlagEvaluationDetails,
    Reason,
)
from openfeature.hook import Hook, HookContext
from openfeature.provider import Metadata, AbstractProvider
from openfeature.exception import ErrorCode

from .types import Evaluation, HyphenEvaluationContext, HyphenProviderOptions, TelemetryPayload
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
                hints: Dict[str, Any]
            ) -> None:
                evaluation = Evaluation(
                    key=details.flag_key,
                    value=details.value,
                    type=hook_context.flag_value_type,
                    reason=details.reason
                )

                context = hook_context.context
                if not isinstance(context, HyphenEvaluationContext):
                    context = HyphenEvaluationContext(
                        targeting_key=context.targeting_key,
                        attributes=context.attributes
                    )

                payload = TelemetryPayload(
                    context=context,
                    data={'toggle': evaluation}
                )

                try:
                    self.provider.hyphen_client.post_telemetry(
                        payload,
                        hook_context.logger
                    )
                except Exception as error:
                    hook_context.logger.error("Unable to log usage", exc_info=error)

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
        attributes = context.attributes if hasattr(context, 'attributes') else {}

        if isinstance(context, HyphenEvaluationContext):
            # Update existing HyphenEvaluationContext
            context.targeting_key = targeting_key
            context.application = self.options.application
            context.environment = self.options.environment
            return context
        else:
            # Create new HyphenEvaluationContext
            return HyphenEvaluationContext(
                targeting_key=targeting_key,
                attributes=attributes,
                application=self.options.application,
                environment=self.options.environment
            )

    def _wrong_type(self, value: Any) -> FlagResolutionDetails:
        """Create an error resolution for wrong type."""
        return FlagResolutionDetails(
            value=value,
            reason=Reason.ERROR,
            error_code=ErrorCode.TYPE_MISMATCH
        )

    def _get_evaluation(
        self,
        flag_key: str,
        context: Optional[EvaluationContext],
        expected_type: str,
        default_value: Any,
        logger: Optional[logging.Logger]
    ) -> Union[Evaluation, FlagResolutionDetails]:
        """Get flag evaluation from the client."""
        try:
            prepared_context = self._prepare_context(context)
            response = self.hyphen_client.evaluate(prepared_context, logger)
            evaluation = response.toggles.get(flag_key)

            if not evaluation or evaluation.error_message:
                raise ValueError(evaluation.error_message if evaluation else "Evaluation does not exist")

            if evaluation.type != expected_type:
                return self._wrong_type(default_value)

            return evaluation

        except Exception as error:
            if logger:
                logger.error(f"Error evaluating flag {flag_key}", exc_info=error)
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.ERROR,
                error_code=ErrorCode.GENERAL
            )

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        context: Optional[EvaluationContext] = None,
        logger: Optional[logging.Logger] = None
    ) -> FlagResolutionDetails[bool]:
        """Resolve boolean flag values."""
        result = self._get_evaluation(flag_key, context, "boolean", default_value, logger)
        if isinstance(result, Evaluation):
            return FlagResolutionDetails(
                value=bool(result.value),
                variant=str(result.value),
                reason=result.reason or Reason.STATIC
            )
        return result

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        context: Optional[EvaluationContext] = None,
        logger: Optional[logging.Logger] = None
    ) -> FlagResolutionDetails[str]:
        """Resolve string flag values."""
        result = self._get_evaluation(flag_key, context, "string", default_value, logger)
        if isinstance(result, Evaluation):
            return FlagResolutionDetails(
                value=str(result.value),
                variant=str(result.value),
                reason=result.reason or Reason.STATIC
            )
        return result

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        context: Optional[EvaluationContext] = None,
        logger: Optional[logging.Logger] = None
    ) -> FlagResolutionDetails[int]:
        """Resolve integer flag values."""
        result = self._get_evaluation(flag_key, context, "number", default_value, logger)
        if isinstance(result, Evaluation):
            return FlagResolutionDetails(
                value=int(result.value),
                variant=str(result.value),
                reason=result.reason or Reason.STATIC
            )
        return result

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        context: Optional[EvaluationContext] = None,
        logger: Optional[logging.Logger] = None
    ) -> FlagResolutionDetails[float]:
        """Resolve float flag values."""
        result = self._get_evaluation(flag_key, context, "number", default_value, logger)
        if isinstance(result, Evaluation):
            return FlagResolutionDetails(
                value=float(result.value),
                variant=str(result.value),
                reason=result.reason or Reason.STATIC
            )
        return result

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: Union[Dict, List],
        context: Optional[EvaluationContext] = None,
        logger: Optional[logging.Logger] = None
    ) -> FlagResolutionDetails[Union[Dict, List]]:
        """Resolve object flag values."""
        result = self._get_evaluation(flag_key, context, "object", default_value, logger)
        if isinstance(result, Evaluation):
            return FlagResolutionDetails(
                value=result.value,
                variant=str(result.value),
                reason=result.reason or Reason.STATIC
            )
        return result
