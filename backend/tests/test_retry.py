from backend.app.services.retry import retry_service

def test_exponential_backoff_calculation():
    # Attempt 1: base (1.0) * 2^0 = 1.0 + jitter [0.1, 0.5] -> range [1.1, 1.5]
    d1 = retry_service.calculate_backoff_delay(1, base_delay=1.0)
    assert 1.0 <= d1 <= 2.0

    # Attempt 2: base (1.0) * 2^1 = 2.0 + jitter -> range [2.1, 3.0]
    d2 = retry_service.calculate_backoff_delay(2, base_delay=1.0)
    assert 2.0 <= d2 <= 3.5

    # Attempt 3: base (1.0) * 2^2 = 4.0 + jitter -> range [4.1, 5.5]
    d3 = retry_service.calculate_backoff_delay(3, base_delay=1.0)
    assert 4.0 <= d3 <= 6.0

    # Max cap check
    d_huge = retry_service.calculate_backoff_delay(15, base_delay=1.0)
    assert d_huge <= 60.0

def test_retryable_classification():
    assert retry_service.is_retryable(500, "Internal Server Error") is True
    assert retry_service.is_retryable(502, "Bad Gateway") is True
    assert retry_service.is_retryable(503, "Service Unavailable") is True
    assert retry_service.is_retryable(429, "Rate Limit Exceeded") is True
    assert retry_service.is_retryable(None, "Connection reset by peer timeout") is True

def test_non_retryable_classification():
    assert retry_service.is_retryable(400, "Bad Request") is False
    assert retry_service.is_retryable(401, "Unauthorized") is False
    assert retry_service.is_retryable(403, "Forbidden") is False
    assert retry_service.is_retryable(422, "Unprocessable Entity") is False
    assert retry_service.is_retryable(None, "Invalid signature detected") is False
