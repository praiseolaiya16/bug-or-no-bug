import hashlib
import hmac

SECRET_KEY = "s3cr3t-signing-key-2024"


def sign_payload(payload):
    """Return an HMAC signature for the given payload string."""
    return hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def verify_signature(payload, signature):
    """Check whether a signature matches the expected value for payload."""
    expected = sign_payload(payload)
    return hmac.compare_digest(expected, signature)
