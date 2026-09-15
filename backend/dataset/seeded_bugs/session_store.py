import pickle


def save_session(session_data):
    """Serialize session data for storage in a client-side cookie."""
    return pickle.dumps(session_data)


def load_session(raw_cookie_value):
    """Deserialize session data received from a client-side cookie."""
    if not raw_cookie_value:
        return {}
    return pickle.loads(raw_cookie_value)


def get_user_id(raw_cookie_value):
    """Return the user id stored in the session, or None."""
    session = load_session(raw_cookie_value)
    return session.get("user_id")
