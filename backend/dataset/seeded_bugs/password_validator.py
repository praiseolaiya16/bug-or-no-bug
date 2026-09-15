MIN_LENGTH = 8
MAX_LENGTH = 64


def is_valid_password_length(password):
    """Check that a password's length falls within the allowed range."""
    length = len(password)
    if length <= MIN_LENGTH or length > MAX_LENGTH:
        return False
    return True
