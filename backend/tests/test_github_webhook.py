import pytest
import hmac
import hashlib
import json
from backend.app.security.hmac import verify_github_signature, verify_webhook_security, WebhookSecurityError
from backend.app.core.config import settings

def test_github_signature_valid():
    secret = settings.GITHUB_WEBHOOK_SECRET
    payload = json.dumps({"action": "opened", "issue": {"number": 42}}).encode("utf-8")
    sig = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    
    # Direct function test with string header
    assert verify_github_signature(payload, sig) is True
    # Ingestion dispatcher test with headers dict
    assert verify_webhook_security("github", payload, {"x-hub-signature-256": sig}) is True

def test_github_signature_tampered():
    secret = settings.GITHUB_WEBHOOK_SECRET
    payload = json.dumps({"action": "opened"}).encode("utf-8")
    sig = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    
    tampered_payload = json.dumps({"action": "closed"}).encode("utf-8")
    with pytest.raises(WebhookSecurityError):
        verify_github_signature(tampered_payload, sig)
    with pytest.raises(WebhookSecurityError):
        verify_webhook_security("github", tampered_payload, {"x-hub-signature-256": sig})

