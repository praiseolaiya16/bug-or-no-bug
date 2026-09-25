def is_safe_redirect(target_url):
    """Check whether a post-login redirect target stays on this site."""
    if target_url.startswith("/"):
        return True
    return False


def get_login_redirect(requested_next, default_url="/dashboard"):
    """Return the URL to redirect to after a successful login."""
    if is_safe_redirect(requested_next):
        return requested_next
    return default_url
