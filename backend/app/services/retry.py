import random
from typing import Optional
from backend.app.core.config import settings

class RetryService:
    @staticmethod
    def calculate_backoff_delay(attempt: int, base_delay: Optional[float] = None) -> float:
        """Calculates exponential backoff with full jitter."""
        base = base_delay if base_delay is not None else settings.BASE_RETRY_DELAY_SEC
        # Exponential component: base * 2^(attempt - 1)
        exp_delay = base * (2 ** max(0, attempt - 1))
        # Add random jitter between 0.1s and 0.5s or 20% of exponential delay
        jitter = random.uniform(0.1, max(0.5, exp_delay * 0.2))
        return min(60.0, exp_delay + jitter)

    @staticmethod
    def is_retryable(status_code: Optional[int], error_message: str) -> bool:
        """
        Classifies errors into RETRYABLE vs NON_RETRYABLE.
        RETRYABLE: 500, 502, 503, 504, 429, timeouts, connection errors.
        NON_RETRYABLE: 400, 401, 403, 404, 422, schema validation failures.
        """
        if status_code is not None:
            if status_code in [500, 502, 503, 504, 429, 408]:
                return True
            if 400 <= status_code < 500 and status_code != 429:
                return False
                
        lower_err = (error_message or "").lower()
        non_retryable_keywords = ["invalid signature", "schema validation", "malformed", "unauthorized", "forbidden"]
        for kw in non_retryable_keywords:
            if kw in lower_err:
                return False
                
        # Timeouts and network blips are retryable by default
        return True

retry_service = RetryService()
