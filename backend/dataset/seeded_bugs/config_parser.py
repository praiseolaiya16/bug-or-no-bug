def parse_config_value(raw_value, default=0):
    """Convert a raw config string into an int, falling back to default."""
    if raw_value is None:
        return default

    try:
        return int(raw_value.strip())
    except:
        return default


def load_config(raw_settings):
    """Parse a dict of raw string settings into integer values."""
    return {key: parse_config_value(value) for key, value in raw_settings.items()}
