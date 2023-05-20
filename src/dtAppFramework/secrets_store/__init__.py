import logging

from ..paths import ApplicationPaths
from ..settings import Settings
from ..misc import singleton
from .local_secret_store import LocalSecretStore
from .aws_secret_store import AWSSecretsStore
from .azure_secret_store import AzureSecretsStore
from enum import Enum


class SecretsManagerScopePriorities(Enum):
    USER = 1
    APP = 2
    AWS = 3
    AZURE = 4


@singleton()
class SecretsManager(object):

    def __init__(self, application_paths=None, application_settings=None) -> None:
        super().__init__()
        self.application_paths = application_paths
        self.application_settings = application_settings
        self.stores = []

        if not self.application_paths:
            self.application_paths = ApplicationPaths()

        if not self.application_settings:
            self.application_settings = Settings()

        self.secrets_manager_settings = self.application_settings.get("secrets_manager", {})
        self.stores.append(LocalSecretStore(store_name="User_Local_Store",
                                            store_priority=SecretsManagerScopePriorities.USER,
                                            root_store_path=self.application_paths.usr_data_root_path))

        try:
            self.stores.append(LocalSecretStore(store_name="App_Local_Store",
                                                store_priority=SecretsManagerScopePriorities.APP,
                                                root_store_path=self.application_paths.app_data_root_path))
        except Exception as ex:
            print(f'Skipping APP Local Secret Store. {ex}')

        if "aws_secrets" in self.secrets_manager_settings:
            self.stores.append(AWSSecretsStore(store_priority=SecretsManagerScopePriorities.AWS,
                                               aws_settings=self.secrets_manager_settings["aws_secrets"]))

        if "azure_secrets" in self.secrets_manager_settings:
            self.stores.append(AzureSecretsStore(store_priority=SecretsManagerScopePriorities.AZURE,
                                                 azure_settings=self.secrets_manager_settings["azure_secrets"]))

        self.stores.sort(key=lambda x: x.priority().value)

    def get_secret(self, key, default_value=None, scope=None):
        value = None
        for store in self.stores:
            if scope and scope == store.priority():
                value = store.get_secret(key, None)
                break
            elif not scope:
                value = store.get_secret(key, None)
                if value:
                    break

        if not value:
            logging.warning(f'The Secret {key} was not found.  Returning default value.')
            value = default_value

        return value

    def set_secret(self, key, value, scope=None):
        if not scope:
            logging.warning("No scope was provided. Setting scope to USER.")
            scope = SecretsManagerScopePriorities.USER

        for store in self.stores:
            if scope == store.priority():
                store.set_secret(key, value)
                break

    def delete_secret(self, key, scope=None):
        if not scope:
            logging.warning("No scope was provided. Setting scope to USER.")
            scope = SecretsManagerScopePriorities.USER

        for store in self.stores:
            if scope and scope == store.priority():
                value = store.delete_secret(key)
                break
