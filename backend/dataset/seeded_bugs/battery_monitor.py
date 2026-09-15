LOW_BATTERY_THRESHOLD = 20
CRITICAL_BATTERY_THRESHOLD = 5


def get_battery_status(battery_percent):
    """Classify the battery level as ok, low, or critical."""
    if battery_percent <= CRITICAL_BATTERY_THRESHOLD:
        return "critical"
    if battery_percent > LOW_BATTERY_THRESHOLD:
        return "low"
    return "ok"
