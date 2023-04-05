import os
import pathlib
import logging
import random
import string
import subprocess
import sys
import re
import pybase64
import boto3
from aws_sso_util import login as aws_sso_util_login

from itertools import cycle
from shutil import copyfile
from pykeepass import PyKeePass
from ..paths import ApplicationPaths
from ..resources import ResourceManager

SECRETS_TEMPLATE = "secrets.store.kdbx"
EMBEDDED_RESOURCES = str(pathlib.Path(__file__).parent.absolute()) + '/../_resources'
SECRETS_STORE_GROUP = "Secrets_Store"
SECRETS_ENV_TAG = "ENV"
SECRETS_HIDDEN_TAG = "HIDDEN"
DEFAULT_PASSWORD = 'password'


class SecretsStoreException(Exception):
    pass


def build_secrets_path(app_paths: ApplicationPaths):
    return f'{app_paths.usr_data_root_path}/secrets.store.kdbx'


class SecretsStore(object):

    def __init__(self, app_paths: ApplicationPaths, resources: ResourceManager,
                 password: str = os.getenv('SECRETS_STORE_PASSWORD', None), aws_profile=None,
                 aws_sso=False) -> None:
        super().__init__()
        self.app_paths = app_paths
        self.resources = resources
        self.resources.add_resource_path(EMBEDDED_RESOURCES)
        self.secrets_store_path = build_secrets_path(self.app_paths)

        try:
            if aws_sso:
                self.run(f'aws sso login --profile {aws_profile}')
            aws_session = boto3.session.Session(profile_name=aws_profile)
            self.aws_secretsmanager = aws_session.client('secretsmanager')
            self.aws_secretsmanager.list_secrets()
        except:
            logging.warning(f'AWS Secrets Manager, Not Available')
            self.aws_secretsmanager = None

        if password is None:
            password = self.guid()

        if not os.path.exists(self.secrets_store_path):
            self.__initialise_secrets_store(password)

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

    def __initialise_secrets_store(self, password):
        try:
            logging.info(f'Creating Secrets Store at: {self.secrets_store_path}')
            copyfile(self.resources.get_resource_path(SECRETS_TEMPLATE), self.secrets_store_path)

            keepass_instance = PyKeePass(self.secrets_store_path, DEFAULT_PASSWORD)
            keepass_instance.password = password
            keepass_instance.add_group(keepass_instance.root_group, SECRETS_STORE_GROUP)
            keepass_instance.save()
            logging.info(f'Successfully created Secrets Store.')
        except Exception as ex:
            logging.error(f'Failed to create Secrets Store.  Error: {str(ex)}')
            raise ex

    def run(self, cmd):
        try:
            return subprocess.run(cmd, shell=True, capture_output=True, check=True, encoding="utf-8") \
                .stdout \
                .strip()
        except:
            return None

    def guid(self):
        base = None
        if sys.platform == 'darwin':
            base = self.run(
                "ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'",
            )

        if sys.platform == 'win32' or sys.platform == 'cygwin' or sys.platform == 'msys':
            base = self.run('wmic csproduct get uuid').split('\n')[2] \
                .strip()

        if sys.platform.startswith('linux'):
            base = self.run('cat /var/lib/dbus/machine-id') or \
                   self.run('cat /etc/machine-id')

        if sys.platform.startswith('openbsd') or sys.platform.startswith('freebsd'):
            base = self.run('cat /etc/hostid') or \
                   self.run('kenv -q smbios.system.uuid')

        if not base:
            raise SecretsStoreException("Failed to determined unique machine ID")

        key = re.sub("[^a-zA-Z]+", "", base)
        xored = ''.join(chr(ord(x) ^ ord(y)) for (x, y) in zip(base, cycle(key)))
        return pybase64.b64encode_as_string(xored.encode())

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
        entry = None
        try:
            if self.aws_secretsmanager:
                entry = self.aws_secretsmanager.get_secret_value(SecretId=name)['SecretString']
        except:
            logging.warning(f'Secret {name} not found in AWS SecretsManager.  Trying Local Instance.')

        if not entry:
            entry = self.keepass_instance.find_entries(title=name, group=self.__store_group(), first=True)

        return entry

    def get_secret(self, name: str) -> str:
        entry = self.get_entry(name)
        if entry is None:
            raise SecretsStoreException(f'Secret {name} does not exists in store.')

        if isinstance(entry, str):
            return entry
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


def get_secret_store(app_paths: ApplicationPaths, resources: ResourceManager, password=None, aws_profile=None,
                     aws_sso=False):
    global secret_store

    if secret_store is None:
        if password is None:
            secret_store = SecretsStore(app_paths=app_paths, resources=resources, aws_profile=aws_profile,
                                        aws_sso=aws_sso)
        else:
            secret_store = SecretsStore(app_paths=app_paths, resources=resources, password=password,
                                        aws_profile=aws_profile, aws_sso=aws_sso)

    return secret_store
