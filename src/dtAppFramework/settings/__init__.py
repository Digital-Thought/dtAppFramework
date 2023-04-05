from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import json
import yaml
import logging
import os

from typing import Union
from ..secrets_store import get_secret_store
from ..paths import ApplicationPaths
from ..resources import ResourceManager

Base = declarative_base()


class Setting(Base):
    """
    The Base Settings Model
    """
    __tablename__ = 'persistent_settings'

    id = Column(Integer, primary_key=True)
    value_name = Column(String(100))
    value = Column(String(1024))
    type = Column(String(24))


class PersistentSettingStore(object):
    """
    A helper class to persist settings to SQL List database at the defined path.
    """

    def __init__(self, path: str) -> None:
        """
        Initialise the persistent settings store.
        SQLite DB will be created at the provided path.
        Will open the existing database if already exists.
        :param path: The path to the SQLite database
        :type path: str
        """
        engine = create_engine(f'sqlite:///{path}?check_same_thread=False')
        Base.metadata.create_all(engine)
        self.DBSession = sessionmaker(bind=engine)
        super().__init__()

    def store(self, key: str, value: Union[str, int, float, dict, bool]) -> Union[str, int, float, dict, bool]:
        """

        :param key:
        :type key:
        :param value:
        :type value:
        :return:
        :rtype:
        """

        if self.get(key=key):
            self.__delete__(key=key)

        session = self.DBSession()
        setting = Setting()
        setting.value_name = key

        if isinstance(value, str):
            setting.type = 'str'
            setting.value = value
        elif isinstance(value, bool):
            setting.type = 'bool'
            setting.value = str(value)
        elif isinstance(value, int):
            setting.type = 'int'
            setting.value = str(value)
        elif isinstance(value, float):
            setting.type = 'float'
            setting.value = str(value)
        elif isinstance(value, dict):
            setting.type = 'dict'
            setting.value = json.dumps(value)
        else:
            raise Exception('Unsupported value type')

        session.add(setting)
        session.commit()
        return value

    def __delete__(self, key: str):
        session = self.DBSession()
        session.query(Setting).filter(Setting.value_name == key).delete()
        session.commit()

    def delete(self, key) -> Union[str, int, float, dict, bool, None]:
        """

        :param key:
        :type key:
        :return:
        :rtype:
        """
        setting = self.get(key)
        if setting is not None:
            self.__delete__(key)
            return setting
        return None

    def get(self, key: str, default: Union[str, int, float, dict, bool, None] = None) -> Union[
        str, int, float, dict, bool, None]:
        """

        :param key:
        :type key:
        :param default:
        :type default:
        :return:
        :rtype:
        """
        session = self.DBSession()
        setting = session.query(Setting).filter(Setting.value_name == key).first()
        if not setting:
            return default

        if setting.type == 'str':
            return setting.value
        elif setting.type == 'int':
            return int(setting.value)
        elif setting.type == 'float':
            return float(setting.value)
        elif setting.type == 'bool':
            return setting.value == 'True'
        elif setting.type == 'dict':
            return json.loads(setting.value)
        else:
            raise Exception('Unsupported value type')


class Configuration(dict):
    """
    Configuration Dictionary for OSINT Platform.
    Configuration can be defined in the YAML file.
    """

    def __init__(self, app_paths: ApplicationPaths) -> None:
        """
        Initialises the configuration settings dictionary.
        """
        self.app_paths = app_paths
        self.app_config_file = f'{self.app_paths.app_data_root_path}/config.yaml'
        self.usr_config_file = f'{self.app_paths.usr_data_root_path}/config.yaml'
        self.app_persistent_settings_store = None
        self.usr_persistent_settings_store = None
        self.reload_yaml()
        self.resource_manager = ResourceManager(app_paths=self.app_paths)

        self.app_persistent_settings_store = PersistentSettingStore(
            path=f'{self.app_paths.app_data_root_path}/persistent.settings')
        self.usr_persistent_settings_store = PersistentSettingStore(
            path=f'{self.app_paths.usr_data_root_path}/persistent.settings')
        super().__init__()

    def load_yaml_file(self, path) -> 'Configuration':
        """
        Loads the specified YAML file into the configuration.
        If a path is not provided, it will use the file path specific when the 'Configuration' was initialised.
        """

        with open(path, 'r', encoding='UTF-8') as file:
            self.update(yaml.safe_load(file))
        return self

    def reload_yaml(self) -> 'Configuration':
        """
        Reloads the configuration from the previously defined YAML file path.
        Note: this will clear all current settings before re-loading.
        :return: Re-loaded configuration
        :rtype: 'Configuration'
        """
        if os.path.exists(self.app_config_file):
            self.load_yaml_file(self.app_config_file)
            logging.info(f'Loaded APP configuration from: {self.app_config_file}')

        if os.path.exists(self.usr_config_file):
            self.load_yaml_file(self.usr_config_file)
            logging.info(f'Loaded USER configuration from: {self.usr_config_file}')

        return self

    def get_requests_tor_proxy(self) -> dict:
        """
        Gets TOR Proxy configuration in a format compatible with Requests
        :return: Dictionary of HTTP and HTTPS configuration for TOR Proxy.
        :rtype: dict
        """
        proxy = self.get('settings.proxies.tor_proxy', '127.0.0.1:9150')
        return {"http": 'socks5h://' + proxy,
                "https": 'socks5h://' + proxy}

    def get_selenium_tor_proxy(self) -> str:
        """
        Gets TOR Proxy configuration in a format compatible with Selenium
        :return: String value for proxy configuration.
        :rtype: str
        """
        proxy = self.get('settings.proxies.tor_proxy', '127.0.0.1:9150')
        return '--proxy-server=socks5://' + proxy

    def set_app_item(self, key, value):
        # if the value of a setting is changed or new setting added,
        # then it will add it to the persistent store and will override any settings in the config YAML.
        return self.app_persistent_settings_store.store(key=key, value=value)

    def __setitem__(self, key, value):
        # if the value of a setting is changed or new setting added,
        # then it will add it to the persistent store and will override any settings in the config YAML.
        return self.usr_persistent_settings_store.store(key=key, value=value)

    def get(self, key, default=None):
        try:
            value = self.__getitem__(key)
            if isinstance(value, str) and str(value).startswith('ENV/'):
                return os.getenv(str(value).replace('ENV/', '').strip(), value)
            if isinstance(value, str) and str(value).startswith('SEC/'):
                return get_secret_store(self.app_paths, resources=self.resource_manager, aws_profile=self.get("secrets_store.aws_profile", None), aws_sso=config.get("secrets_store.aws_sso", False)).get_secret(str(value).replace('SEC/', '').strip())
            if not value:
                return default
            return value
        except KeyError:
            return default

    def get_secret(self, key, default=None):
        try:
            return get_secret_store(self.app_paths, resources=self.resource_manager, aws_profile=self.get("secrets_store.aws_profile", None), aws_sso=config.get("secrets_store.aws_sso", False)).get_secret(key)
        except:
            logging.warning(f"Secret '{key}' not found. Returning default.")
            return default

    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError("object has no attribute '%s'" % key)

    def __getitem__(self, key):
        persistent_value = None
        if self.app_persistent_settings_store:
            persistent_value = self.app_persistent_settings_store.get(key)
        if self.usr_persistent_settings_store:
            persistent_value = self.usr_persistent_settings_store.get(key)
        if persistent_value is not None:
            return persistent_value
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


config: Union[Configuration, None] = None
"""
The loaded Configuration.  This will be None until load(path) is called.
"""


def load(path: ApplicationPaths) -> Configuration:
    """
    Loads the configuration from the YAML file.
    If the YAML file is not specified in 'path' the default location is used: './config/osint_config.yaml'
    :param path: Path to the YAML file with the configuration.  If not provided, the default DEFAULT_CONFIG_LOCATION used
    :type path: str
    :return: The loaded configuration
    :rtype: Configuration
    """
    global config
    config = Configuration(app_paths=path)
    return config
