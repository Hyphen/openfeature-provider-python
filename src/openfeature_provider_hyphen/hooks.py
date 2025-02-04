from openfeature.hook import Hook, HookContext
from openfeature.flag_evaluation import FlagEvaluationDetails

from .types import TelemetryPayload

class TelemetryHook(Hook):
    """Hook for tracking feature flag usage telemetry."""
    
    def __init__(self, provider):
        """Initialize the telemetry hook.
        
        Args:
            provider: The HyphenProvider instance
        """
        self.provider = provider

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
        """
        print("Hook after")
        context = self.provider._prepare_context(hook_context.evaluation_context)
        payload = TelemetryPayload(
            context=context,
            data={'toggle': details}
        )

        try:
            self.provider.hyphen_client.post_telemetry(payload)
        except Exception as error:
            print("Unable to log usage", error)
