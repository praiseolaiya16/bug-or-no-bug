from datetime import date


class DateRange:
    """A date range that is inclusive of both its start and end dates."""

    def __init__(self, start: date, end: date):
        self.start = start
        self.end = end

    def duration_days(self):
        """Return the number of days spanned by this inclusive range."""
        return (self.end - self.start).days

    def contains(self, day: date) -> bool:
        """Return whether the given day falls within this range."""
        return self.start <= day <= self.end
