import time
import pytest
from backend.app.security.hmac import (
    generate_stripe_signature,
    verify_stripe_signature,
    generate_razorpay_signature,
    verify_razorpay_signature,
    generate_github_signature,
    verify_github_signature,
    WebhookSecurityError
)

def test_stripe_signature_valid():
    payload = b'{"id":"evt_test_123","type":"payment_intent.succeeded"}'
    secret = "whsec_test_secret"
    sig_header = generate_stripe_signature(payload, secret)
    assert verify_stripe_signature(payload, sig_header, secret=secret) is True

def test_stripe_signature_tampered_payload():
    payload = b'{"id":"evt_test_123","amount":1000}'
    tampered = b'{"id":"evt_test_123","amount":9999}'
    secret = "whsec_test_secret"
    sig_header = generate_stripe_signature(payload, secret)
    with pytest.raises(WebhookSecurityError) as exc:
        verify_stripe_signature(tampered, sig_header, secret=secret)
    assert "Invalid Stripe HMAC-SHA256" in str(exc.value)

def test_stripe_signature_replay_attack_expired():
    payload = b'{"id":"evt_test_123"}'
    secret = "whsec_test_secret"
    old_timestamp = int(time.time()) - 400 # 400 seconds ago > 300s tolerance
    sig_header = generate_stripe_signature(payload, secret, timestamp=old_timestamp)
    with pytest.raises(WebhookSecurityError) as exc:
        verify_stripe_signature(payload, sig_header, secret=secret, tolerance_seconds=300)
    assert "replay attack protection" in str(exc.value)

def test_razorpay_signature_valid():
    payload = b'{"event":"payment.captured","payload":{"payment":{"id":"pay_123"}}}'
    secret = "rzp_secret_123"
    sig = generate_razorpay_signature(payload, secret)
    assert verify_razorpay_signature(payload, sig, secret=secret) is True

def test_razorpay_signature_invalid():
    payload = b'{"event":"payment.captured"}'
    secret = "rzp_secret_123"
    with pytest.raises(WebhookSecurityError):
        verify_razorpay_signature(payload, "invalid_signature_hash", secret=secret)

def test_github_signature_valid():
    payload = b'{"action":"opened","issue":{"number":1}}'
    secret = "gh_secret_123"
    sig = generate_github_signature(payload, secret)
    assert verify_github_signature(payload, sig, secret=secret) is True

def test_github_signature_missing():
    payload = b'{"action":"opened"}'
    with pytest.raises(WebhookSecurityError) as exc:
        verify_github_signature(payload, None, secret="gh_secret_123")
    assert "Missing X-Hub-Signature-256" in str(exc.value)
