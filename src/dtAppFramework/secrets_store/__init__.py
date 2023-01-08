import os
import pathlib
import logging
import random
import string

from shutil import copyfile
from pykeepass import PyKeePass
from ..paths import ApplicationPaths

SECRETS_TEMPLATE = str(pathlib.Path(__file__).parent.absolute()) + '/../_resources/secrets.store.kdbx'
SECRETS_STORE_GROUP = "Secrets_Store"
SECRETS_ENV_TAG = "ENV"
SECRETS_HIDDEN_TAG = "HIDDEN"
DEFAULT_PASSWORD = 'password'


class SecretsStoreException(Exception):
    pass


def build_secrets_path(app_paths: ApplicationPaths):
    return f'{app_paths.usr_data_root_path}/secrets.store.kdbx'


class SecretsStore(object):

    def __init__(self, app_paths: ApplicationPaths, password: str = os.getenv('SECRETS_STORE_PASSWORD', None)) -> None:
        super().__init__()
        self.app_paths = app_paths
        self.secrets_store_path = build_secrets_path(self.app_paths)
        if not os.path.exists(self.secrets_store_path):
            raise SecretsStoreException(f'A Secrets Store does not exists at: {self.secrets_store_path}.')

        if not password:
            raise SecretsStoreException('No password was provided for Secrets Store.  '
                                        'Password must be provided or environment variable SECRETS_STORE_PASSWORD set.')

        try:
            self.keepass_instance = PyKeePass(self.secrets_store_path, password)
            self.__set_environment_variables()
        except Exception as ex:
            raise SecretsStoreException(f'Failed to open Secrets Store: {str(ex)}')

        logging.info(f'Successfully opened Secrets Store: {self.secrets_store_path}')

    def __store_group(self):
        return self.keepass_instance.find_groups(name=SECRETS_STORE_GROUP, first=True)

    def __set_environment_variables(self):
        for entry in self.__store_group().entries:
            if entry.username == SECRETS_ENV_TAG:
                os.environ[entry.title] = entry.password

    def add_secret(self, name: str, secret: str, init_env: bool = False, hidden: bool = False):
        if self.get_entry(name):
            self.delete_entry(name)

        if init_env and hidden:
            raise SecretsStoreException(f' Entry "{name}" can not be both HIDDEN and ENVIRONMENT initialised.')

        tag = '-'
        if init_env:
            tag = SECRETS_ENV_TAG
        if hidden:
            tag = SECRETS_HIDDEN_TAG

        self.keepass_instance.add_entry(self.__store_group(), name, tag, secret)

        self.save()

    def create_secret(self, name: str, init_env: bool = False, hidden: bool = False, length: int = 10) -> str:
        lower = string.ascii_lowercase
        upper = string.ascii_uppercase
        numbers = string.digits
        symbols = string.punctuation

        secret = random.sample(lower + upper + numbers + symbols, length)
        secret = "".join(secret)

        self.add_secret(name=name, secret=secret, init_env=init_env, hidden=hidden)
        return secret

    def delete_entry(self, name):
        entry = self.keepass_instance.find_entries(title=name, group=self.__store_group(), first=True)
        entry.delete()
        self.save()

    def get_entry(self, name: str):
        entry = self.keepass_instance.find_entries(title=name, group=self.__store_group(), first=True)
        return entry

    def get_secret(self, name: str) -> str:
        entry = self.get_entry(name)
        if entry is None:
            raise SecretsStoreException(f'Secret {name} does not exists in store.')

        return entry.password

    def get_secret_names(self, exclude_hidden: bool = True) -> list:
        secret_keys = []
        for entry in self.__store_group().entries:
            if not (entry.username == SECRETS_HIDDEN_TAG and exclude_hidden):
                secret_keys.append(entry.title)
        return secret_keys

    def save(self):
        self.keepass_instance.save()

    def close(self):
        self.save()


secret_store: SecretsStore = None


def get_secret_store(app_paths: ApplicationPaths, password=None):
    global secret_store

    if secret_store is None:
        if password is None:
            secret_store = SecretsStore(app_paths=app_paths)
        else:
            secret_store = SecretsStore(app_paths=app_paths, password=password)

    return secret_store


def initialise_new_secrets_store(app_paths: ApplicationPaths, password: str = os.getenv('SECRETS_STORE_PASSWORD', None)):
    if password is None:
        raise SecretsStoreException('No password was provided for new Secrets Store.  '
                                    'Password must be provided or environment variable SECRETS_STORE_PASSWORD set.')

    secrets_path = build_secrets_path(app_paths)
    if os.path.exists(secrets_path):
        raise SecretsStoreException(f'A Secrets Store already exists at: {secrets_path}.')

    try:
        logging.info(f'Creating Secrets Store at: {secrets_path}')
        copyfile(SECRETS_TEMPLATE, secrets_path)

        keepass_instance = PyKeePass(secrets_path, DEFAULT_PASSWORD)
        keepass_instance.password = password
        keepass_instance.add_group(keepass_instance.root_group, SECRETS_STORE_GROUP)
        keepass_instance.save()
        logging.info(f'Successfully created Secrets Store.')
    except Exception as ex:
        logging.error(f'Failed to create Secrets Store.  Error: {str(ex)}')
        raise ex
