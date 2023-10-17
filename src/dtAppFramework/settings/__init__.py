from ..paths import ApplicationPaths
from ..misc import singleton
from .settings_reader import SettingsReader
from .persistent_settings import PersistentSettingStore, PersistentSettingScope

import os


@singleton()
class Settings(dict):

    def __init__(self, application_paths=None) -> None:
        self.application_paths = application_paths
        if not self.application_paths:
            self.application_paths = ApplicationPaths()

        self.settings_readers = []
        self.persistent_settings_stores = []

        self.init_settings_readers()
        self.init_persistent_settings_stores()
        super().__init__()

    def init_settings_readers(self):
        self.settings_readers.append(SettingsReader(os.path.join(os.getcwd(), "config"), 300))
        self.settings_readers.append(SettingsReader(self.application_paths.app_data_root_path, 200))
        self.settings_readers.append(SettingsReader(self.application_paths.usr_data_root_path, 100))
        self.settings_readers.sort(key=lambda x: x.priority)

    def init_persistent_settings_stores(self):
        try:
            self.persistent_settings_stores.append(PersistentSettingStore(self.application_paths.app_data_root_path,
                                                                          PersistentSettingScope.APP))
        except Exception as ex:
            print(f'Skipping support for application scope persistent store. {ex}')
        self.persistent_settings_stores.append(PersistentSettingStore(self.application_paths.usr_data_root_path,
                                                                      PersistentSettingScope.USER))
        self.persistent_settings_stores.sort(key=lambda x: x.priority.value)

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

    def get(self, key, default=None):
        try:
            value = self.__getitem__(key)
            if isinstance(value, str) and str(value).startswith('ENV/'):
                return os.getenv(str(value).replace('ENV/', '').strip(), value)
            if isinstance(value, str) and str(value).startswith('SEC/'):
                from ..secrets_store import SecretsManager
                return SecretsManager().get_secret(str(value).replace('SEC/', '').strip(), default)
            #AWS_Secret
            if isinstance(value, str) and str(value).startswith('AWS_Secret#'):
                from ..secrets_store import SecretsManager
                return SecretsManager().get_secret(str(value).strip(), default)
            if not value:
                return default
            return value
        except KeyError:
            return default

    def set(self, key, value, scope=PersistentSettingScope.USER):
        for persistent_store in self.persistent_settings_stores:
            if persistent_store.priority == scope:
                persistent_store.store(key, value)
                break

    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError("object has no attribute '%s'" % key)

    def __setitem__(self, key, value):
        # if the value of a setting is changed or new setting added,
        # then it will add it to the persistent store and will override any settings in the config YAML.
        return self.set(key=key, value=value)

    def __getitem__(self, key):
        for persistent_store in self.persistent_settings_stores:
            persistent_value = persistent_store.get(key)
            if persistent_value:
                return persistent_value

        value = None
        for reader in self.settings_readers:
            value = reader.__getitem__(key)
            if value:
                break

        return value
