from functools import wraps
from typing import Any

import subprocess
import logging


def singleton(key_name: str = None) -> Any:
    """
    Decorator to create a singleton class. If a key is passed, it will allow
    for multiple instances of the same singleton to exist.

    :param key_name: The name of the key to monitor for multiple
    instances
    """

    def wrap(class_: Any) -> Any:
        instances = {}

        @wraps(class_)
        def get_instance(*args: dict, **kwargs: dict) -> Any:
            # Get key to monitor
            key_to_monitor_value = kwargs.get(key_name, "GLOBAL")
            class_key = f"{class_}_{key_name}_{key_to_monitor_value}"
            # Create instance if it doesn't exist
            if class_key not in instances:
                instances[class_key] = class_(*args, **kwargs)
            return instances[class_key]

        return get_instance

    return wrap


def run_cmd(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, check=True, encoding="utf-8") \
            .stdout \
            .strip()
    except Exception as ex:
        logging.exception(str(ex))
        return None