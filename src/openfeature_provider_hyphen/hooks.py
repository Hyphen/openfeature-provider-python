import logging

from openfeature.flag_evaluation import FlagEvaluationDetails
from openfeature.hook import Hook, HookContext

from .types import TelemetryPayload
from .utils import prepare_evaluate_payload, prepare_telemetry_details

logger = logging.getLogger(__name__)


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
            hints: Additional hints from the evaluation process
        """
        context = self.provider._prepare_context(hook_context.evaluation_context)
        context_dict = prepare_evaluate_payload(context)
        details_dict = prepare_telemetry_details(details)

        payload = TelemetryPayload(context=context_dict, data={"toggle": details_dict})

        try:
            self.provider.hyphen_client.post_telemetry(payload)
        except Exception as error:
            logger.error("Unable to log usage: %s", error)
