import yaml


def load_user_config(config_text):
    """Parse a YAML config string uploaded by a user."""
    return yaml.load(config_text)


def load_config_file(path):
    """Load and parse a YAML config file from disk."""
    with open(path) as f:
        return load_user_config(f.read())
