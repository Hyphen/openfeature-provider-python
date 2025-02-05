from openfeature.hook import Hook, HookContext
from openfeature.flag_evaluation import FlagEvaluationDetails

from .types import TelemetryPayload
from .utils import transform_dict_keys

class TelemetryHook(Hook):
    """Hook for tracking feature flag usage telemetry."""
    
    def __init__(self, provider):
        """Initialize the telemetry hook.
        
        Args:
            provider: The HyphenProvider instance
        """
        self.provider = provider

    def _serialize_details(self, details: FlagEvaluationDetails, hints: dict) -> dict:
        """Convert FlagEvaluationDetails to a serializable dictionary.
        
        Args:
            details: The flag evaluation details
            hints: Additional hints from the evaluation process
            
        Returns:
            A dictionary representation of the details
        """
        return {
            "key": details.flag_key,
            "type": hints.get("flag_type", "unknown"),
            "value": details.value,
            "reason": details.reason,
            "errorMessage": details.error_message
        }

    def after(
        self,
        hook_context: HookContext,
        details: FlagEvaluationDetails,
        hints: dict,
    ) -> None:
        """Process telemetry after flag evaluation.
        
        Args:
            hook_context: Context for the hook execution
            details: Details about the flag evaluation
            hints: Additional hints from the evaluation process
        """
        context = self.provider._prepare_context(hook_context.evaluation_context)
        
        # Convert context to dict and handle attributes
        context_dict = context.__dict__.copy()
        if 'attributes' in context_dict and context_dict['attributes']:
            attributes = context_dict.pop('attributes')
            context_dict.update(attributes)
        context_dict.pop('attributes', None)
        
        # Transform keys to camelCase
        context_dict = transform_dict_keys(context_dict)
        
        # Convert details to serializable format
        details_dict = self._serialize_details(details, hints)
        
        payload = TelemetryPayload(
            context=context_dict,
            data={'toggle': details_dict}
        )

        print("Logging usage:", payload)

        try:
            self.provider.hyphen_client.post_telemetry(payload)
        except Exception as error:
            print("Unable to log usage", error)
