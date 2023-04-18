import json


import yaml
import logging
import os


class SettingsReader(dict):

    def __init__(self, path: str, priority: int) -> None:
        self.priority = priority
        self.settings_file = os.path.join(path, "config.yaml")

        if os.path.exists(self.settings_file):
            self.load_yaml_file()

        super().__init__()

    def load_yaml_file(self):
        with open(self.settings_file, 'r', encoding='UTF-8') as file:
            self.update(yaml.safe_load(file))

    def clear(self) -> None:
        raise NotImplemented

    def popitem(self):
        raise NotImplemented

    def __setitem__(self, k, v) -> None:
        raise NotImplemented

    def pop(self, __key):
        raise NotImplemented

    def __getitem__(self, key):
        keys = key.split('.')
        if len(keys) == 1:
            return dict.__getitem__(self, key)
        else:
            data = self.copy()
            for key in keys:
                if key in data:
                    data = data[key]
                else:
                    return None
            return data