import hashlib


def hash_password(password):
    """Return a hash of the given plaintext password for storage."""
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(password, stored_hash):
    """Check whether a plaintext password matches the stored hash."""
    return hash_password(password) == stored_hash
