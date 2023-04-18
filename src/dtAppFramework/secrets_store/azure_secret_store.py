from .secret_store import AbstractSecretStore, SecretsStoreException
from shutil import which
from ..misc import run_cmd
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

import logging


class AzureSecretsStore(AbstractSecretStore):

    def __init__(self, store_priority, azure_settings) -> None:
        super().__init__("Azure_Secrets_Store", store_priority)
        if not which("az"):
            raise SecretsStoreException("Azure Secrets Store requires the Azure Command Line Utility to be installed.")
        self.azure_keyvault_name = azure_settings.get('keyvault_name', None)

        if not self.azure_keyvault_name:
            raise SecretsStoreException("Azure Secrets Store requires a valid key vault name to be provided.")

        self.kv_uri = f"https://{self.azure_keyvault_name}.vault.azure.net"
        try:
            credential = DefaultAzureCredential()
            self.azure_client = SecretClient(vault_url=self.kv_uri, credential=credential)
        except Exception as ex:
            raise SecretsStoreException(f'Azure Secrets Store, Not Available. Error: {str(ex)}')

    def get_secret(self, key, default_value=None):
        try:
            entry = self.azure_client.get_secret(key)
        except Exception as ex:
            logging.error(str(ex))
            entry = None

        if not entry:
            entry = default_value

        return entry

    def set_secret(self, key, value):
        try:
            self.azure_client.set_secret(key, value)
        except Exception as ex:
            logging.error(str(ex))
            raise SecretsStoreException(str(ex))

    def delete_secret(self, key):
        try:
            poller = self.azure_client.begin_delete_secret(key)
            deleted_secret = poller.result()
        except Exception as ex:
            logging.error(str(ex))
            raise SecretsStoreException(str(ex))


