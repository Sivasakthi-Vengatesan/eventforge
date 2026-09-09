import hmac
import hashlib
import time
from typing import Optional, Tuple
from backend.app.core.config import settings

class WebhookSecurityError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

def compute_hmac_sha256(key: str, message: bytes) -> str:
    return hmac.new(key.encode("utf-8"), message, hashlib.sha256).hexdigest()

def generate_stripe_signature(raw_body: bytes, secret: str, timestamp: Optional[int] = None) -> str:
    ts = timestamp or int(time.time())
    payload_to_sign = f"{ts}.".encode("utf-8") + raw_body
    sig = compute_hmac_sha256(secret, payload_to_sign)
    return f"t={ts},v1={sig}"

def generate_razorpay_signature(raw_body: bytes, secret: str) -> str:
    return compute_hmac_sha256(secret, raw_body)

def generate_github_signature(raw_body: bytes, secret: str) -> str:
    sig = compute_hmac_sha256(secret, raw_body)
    return f"sha256={sig}"

def generate_generic_signature(raw_body: bytes, secret: str) -> str:
    return compute_hmac_sha256(secret, raw_body)

def verify_stripe_signature(
    raw_body: bytes,
    signature_header: Optional[str],
    secret: str = settings.WEBHOOK_SECRET_STRIPE,
    tolerance_seconds: int = 300
) -> bool:
    if not signature_header:
        raise WebhookSecurityError("Missing Stripe-Signature header", status_code=401)
    
    pairs = signature_header.split(",")
    header_data = {}
    for pair in pairs:
        parts = pair.strip().split("=", 1)
        if len(parts) == 2:
            header_data[parts[0]] = parts[1]
            
    timestamp_str = header_data.get("t")
    signature = header_data.get("v1")
    
    if not timestamp_str or not signature:
        raise WebhookSecurityError("Malformed Stripe-Signature header", status_code=401)
        
    try:
        timestamp = int(timestamp_str)
    except ValueError:
        raise WebhookSecurityError("Invalid timestamp in Stripe-Signature", status_code=401)
        
    # Replay protection
    current_time = int(time.time())
    if abs(current_time - timestamp) > tolerance_seconds:
        raise WebhookSecurityError("Stripe webhook timestamp out of tolerance window (replay attack protection)", status_code=401)
        
    expected_payload = f"{timestamp}.".encode("utf-8") + raw_body
    expected_sig = compute_hmac_sha256(secret, expected_payload)
    
    if not hmac.compare_digest(expected_sig, signature):
        raise WebhookSecurityError("Invalid Stripe HMAC-SHA256 signature", status_code=403)
        
    return True

def verify_razorpay_signature(
    raw_body: bytes,
    signature_header: Optional[str],
    secret: str = settings.WEBHOOK_SECRET_RAZORPAY
) -> bool:
    if not signature_header:
        raise WebhookSecurityError("Missing X-Razorpay-Signature header", status_code=401)
        
    expected_sig = compute_hmac_sha256(secret, raw_body)
    if not hmac.compare_digest(expected_sig, signature_header):
        raise WebhookSecurityError("Invalid Razorpay HMAC-SHA256 signature", status_code=403)
        
    return True

def verify_github_signature(
    raw_body: bytes,
    signature_header: Optional[str],
    secret: str = settings.WEBHOOK_SECRET_GITHUB
) -> bool:
    if not signature_header:
        raise WebhookSecurityError("Missing X-Hub-Signature-256 header", status_code=401)
        
    if not signature_header.startswith("sha256="):
        raise WebhookSecurityError("Malformed X-Hub-Signature-256 header format", status_code=401)
        
    signature = signature_header.split("sha256=", 1)[1]
    expected_sig = compute_hmac_sha256(secret, raw_body)
    
    if not hmac.compare_digest(expected_sig, signature):
        raise WebhookSecurityError("Invalid GitHub HMAC-SHA256 signature", status_code=403)
        
    return True

def verify_generic_signature(
    raw_body: bytes,
    signature_header: Optional[str],
    secret: str = settings.WEBHOOK_SECRET_GENERIC
) -> bool:
    if not signature_header:
        # Generic may allow optional auth or fallback
        return True
    
    clean_sig = signature_header.replace("sha256=", "").strip()
    expected_sig = compute_hmac_sha256(secret, raw_body)
    
    if not hmac.compare_digest(expected_sig, clean_sig):
        raise WebhookSecurityError("Invalid Generic HMAC-SHA256 signature", status_code=403)
        
    return True

def verify_webhook_security(
    provider: str,
    raw_body: bytes,
    headers: dict
) -> bool:
    """Dispatches signature verification for provider with unified error handling."""
    provider_lower = provider.lower()
    if provider_lower == "stripe":
        return verify_stripe_signature(raw_body, headers.get("stripe-signature"))
    elif provider_lower == "razorpay":
        return verify_razorpay_signature(raw_body, headers.get("x-razorpay-signature"))
    elif provider_lower == "github":
        return verify_github_signature(raw_body, headers.get("x-hub-signature-256"))
    elif provider_lower == "generic":
        return verify_generic_signature(raw_body, headers.get("x-signature-256") or headers.get("x-signature"))
    else:
        return True
