import logging
import time
from datetime import datetime
from openfeature.evaluation_context import EvaluationContext
from openfeature import api
from openfeature_provider_hyphen import HyphenProvider, HyphenProviderOptions
from openfeature_provider_hyphen.hyphen_client import HyphenClient


def custom_cache_key_fn(context: EvaluationContext) -> str:
    targeting_key = context.targeting_key
    email = context.attributes.get("user", {}).get("email", "")
    cache_key = f"{targeting_key}:{email}"
    return cache_key


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",  # Simplified format for cleaner output
    )
    logger = logging.getLogger(__name__)

    # Provider options
    options = HyphenProviderOptions(
        application="app-name",
        environment="env-name",
        enable_toggle_usage=True,
        # generate_cache_key_fn=custom_cache_key_fn,
        cache_ttl_seconds=10,
    )

    try:
        provider = HyphenProvider(
            public_key="<your-public-key>",
            options=options,
        )
    except Exception as e:
        logger.fatal(f"Failed to initialize provider: {e}")
        return

    api.set_provider(provider)
    client = api.get_client("basic-example")

    eval_ctx = EvaluationContext(
        targeting_key="user-123",
        attributes={
            "user": {
                "email": "example@gmail.com",
                "id": "user-123",
                "name": "John Doe",
                "custom_attributes": {"role": "admin"},
            }
        },
    )

    flag_key = "bool-test"
    default_value = False

    try:
        logger.info("\n" + "=" * 80)
        logger.info("FEATURE FLAG CACHING DEMONSTRATION")
        logger.info("=" * 80)

        # First call
        current_time = datetime.now().strftime("%H:%M:%S")
        logger.info(f"\n[{current_time}] FIRST API CALL")
        logger.info("--> Checking cache... (No cache entry found)")
        logger.info("--> Making API request to Hyphen server...")
        result1 = client.get_boolean_value(flag_key, default_value, eval_ctx)
        logger.info(
            f"--> Response received: Feature flag '{flag_key}' = {result1}"
        )
        logger.info("--> Storing result in cache...")

        # Second call after 2 seconds
        time.sleep(2)
        current_time = datetime.now().strftime("%H:%M:%S")
        logger.info(f"\n[{current_time}] SECOND API CALL (After 2 seconds)")
        logger.info("--> Checking cache... (Cache entry found!)")
        logger.info("--> Using cached value (No API request needed)")
        result2 = client.get_boolean_value(flag_key, default_value, eval_ctx)
        logger.info(f"--> Cached value: Feature flag '{flag_key}' = {result2}")

        # Third call after 5 seconds
        time.sleep(5)
        current_time = datetime.now().strftime("%H:%M:%S")
        logger.info(f"\n[{current_time}] THIRD API CALL (After 7 seconds)")
        logger.info("--> Checking cache... (Cache entry found!)")
        logger.info("--> Using cached value (No API request needed)")
        result3 = client.get_boolean_value(flag_key, default_value, eval_ctx)
        logger.info(f"--> Cached value: Feature flag '{flag_key}' = {result3}")

        # Fourth call after 12 seconds
        time.sleep(12)
        current_time = datetime.now().strftime("%H:%M:%S")
        logger.info(f"\n[{current_time}] FOURTH API CALL (After 19 seconds)")
        logger.info("--> Checking cache... (Cache expired!)")
        logger.info("--> Making new API request to Hyphen server...")
        result4 = client.get_boolean_value(flag_key, default_value, eval_ctx)
        logger.info(
            f"--> New response received: Feature flag '{flag_key}' = {result4}"
        )
        logger.info("--> Storing new result in cache...")

        logger.info("\n" + "=" * 80)
        logger.info("DEMONSTRATION COMPLETE")
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"\n[ERROR] An error occurred: {e}")


if __name__ == "__main__":
    main()
