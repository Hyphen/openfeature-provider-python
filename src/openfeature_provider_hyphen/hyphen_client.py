import logging
from typing import Dict, Optional
import requests

from .types import EvaluationResponse, HyphenEvaluationContext, HyphenProviderOptions, TelemetryPayload, Evaluation
from .cache_client import CacheClient
from .utils import build_default_horizon_url, build_url, transform_dict_keys

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
        self.horizon_urls = [*(options.horizon_urls or []), self.default_horizon_url]
        self.cache = CacheClient(
            ttl_seconds=options.cache_ttl_seconds or 30
        )
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'x-api-key': public_key
        })

    def _try_urls(self, url_path: str, payload: Dict, logger: Optional[logging.Logger] = None) -> requests.Response:
        """Try to make a request to each URL until one succeeds.
        
        Args:
            url_path: The API endpoint path
            payload: The request payload
            logger: Optional logger for debug information
            
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
                if logger:
                    logger.debug(f'Failed to fetch: {url}', exc_info=error)
                continue
        
        raise last_error or Exception("All URLs failed")

    def evaluate(
        self, 
        context: HyphenEvaluationContext, 
        logger: Optional[logging.Logger] = None
    ) -> EvaluationResponse:
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

        # Prepare payload
        payload = context.__dict__.copy()
        if 'attributes' in payload and payload['attributes']:
            attributes = payload.pop('attributes')
            payload.update(attributes)
        payload.pop('attributes', None)
        
        # Convert keys to camelCase
        payload = transform_dict_keys(payload)

        # Make API request
        response = self._try_urls('/toggle/evaluate', payload, logger)
        response_data = response.json()
        
        # Convert raw response to EvaluationResponse
        toggles = {}
        for key, value in response_data.get('toggles', {}).items():
            toggles[key] = Evaluation(
                key=key,
                value=value.get('value'),
                type=value.get('type'),
                reason=value.get('reason'),
                error_message=value.get('errorMessage'),
                variant=value.get('variant')
            )
        
        evaluation_response = EvaluationResponse(toggles=toggles)

        # Cache the response
        if evaluation_response:
            self.cache.set(context, evaluation_response)

        return evaluation_response

    def post_telemetry(
        self, 
        payload: TelemetryPayload,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Send telemetry data to the API.
        
        Args:
            payload: The telemetry payload to send
            logger: Optional logger for debug information
        """
        telemetry_payload = payload.__dict__.copy()
        telemetry_payload = transform_dict_keys(telemetry_payload)
        self._try_urls('/toggle/telemetry', telemetry_payload, logger)
