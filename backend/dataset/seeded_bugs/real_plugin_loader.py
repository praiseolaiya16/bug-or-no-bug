import importlib


def load_plugin(module_name):
    """Import a plugin module by name, returning None if it fails to load."""
    try:
        return importlib.import_module(module_name)
    except:
        return None


def load_all_plugins(module_names):
    """Import every plugin in the list, skipping any that fail."""
    return [load_plugin(name) for name in module_names if load_plugin(name) is not None]
