import logging
from typing import Dict

import requests

from .cache_client import CacheClient
from .types import (Evaluation, EvaluationResponse, HyphenEvaluationContext,
                    HyphenProviderOptions, TelemetryPayload)
from .utils import (build_default_horizon_url, build_url,
                    prepare_evaluate_payload, transform_dict_keys)

logger = logging.getLogger(__name__)


class HyphenClient:
    """Client for interacting with the Hyphen API."""

    def __init__(self, public_key: str, options: HyphenProviderOptions):
        """Initialize the Hyphen client.

        Args:
            public_key: The public API key for authentication
            options: Configuration options for the client
        """
        self.public_key = public_key
        self.default_horizon_url = build_default_horizon_url(public_key)
        self.horizon_urls = [
            *(options.horizon_urls or []),
            *(self.default_horizon_url,),
        ]
        self.cache = CacheClient(
            ttl_seconds=options.cache_ttl_seconds or 30,
            generate_cache_key_fn=options.generate_cache_key_fn,
        )
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "x-api-key": public_key}
        )

    def _try_urls(self, url_path: str, payload: Dict) -> requests.Response:
        """Try to make a request to each URL until one succeeds.

        Args:
            url_path: The API endpoint path
            payload: The request payload

        Returns:
            The successful response

        Raises:
            Exception: If all URLs fail
        """
        last_error = None

        for base_url in self.horizon_urls:
            try:
                url = build_url(base_url, url_path)
                response = self.session.post(url, json=payload)
                response.raise_for_status()
                return response
            except Exception as error:
                last_error = error
                continue

        raise last_error or Exception("Something went wrong")

    def evaluate(self, context: HyphenEvaluationContext) -> EvaluationResponse:
        """Evaluate feature flags for the given context.

        Args:
            context: The evaluation context
            logger: Optional logger for debug information

        Returns:
            The evaluation response containing flag values
        """
        # Check cache first
        cached_response = self.cache.get(context)
        if cached_response:
            return cached_response

        # Prepare payload for evaluation
        payload = prepare_evaluate_payload(context)

        # Make API request
        response = self._try_urls("/toggle/evaluate", payload)
        response_data = response.json()

        # Convert raw response to EvaluationResponse
        toggles = {}
        for key, value in response_data.get("toggles", {}).items():
            toggles[key] = Evaluation(
                key=key,
                value=value.get("value"),
                type=value.get("type"),
                reason=value.get("reason"),
                error_message=value.get("errorMessage"),
                variant=value.get("variant"),
            )

        evaluation_response = EvaluationResponse(toggles=toggles)

        # Cache the response
        if evaluation_response:
            self.cache.set(context, evaluation_response)

        return evaluation_response

    def post_telemetry(self, payload: TelemetryPayload) -> None:
        """Send telemetry data to the API.

        Args:
            payload: The telemetry payload to send
        """
        try:
            telemetry_payload = payload.__dict__.copy()
            telemetry_payload = transform_dict_keys(telemetry_payload)
            self._try_urls("/toggle/telemetry", telemetry_payload)
        except Exception as e:
            logger.debug("Error sending telemetry: %s", e)
