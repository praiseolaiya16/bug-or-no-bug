class RetryTracker:
    """Tracks retry attempts for a flaky operation."""

    def __init__(self, max_retries=3):
        self.max_retries = max_retries
        self.attempts = 0

    def record_attempt(self):
        """Record an attempt and return whether retries are still allowed."""
        self.attempts += 1
        return self.attempts <= self.max_retries

    def reset_on_success(self):
        """Reset the tracker after a successful operation."""
        pass
