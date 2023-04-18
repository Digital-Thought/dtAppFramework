import string
import random


class AbstractSecretStore(object):

    def __init__(self, store_name, store_priority) -> None:
        super().__init__()
        self.store_name = store_name
        self.store_priority = store_priority

    def priority(self):
        return self.store_priority

    def name(self):
        return self.store_name

    def __str__(self) -> str:
        return f'{self.store_name}-SecretStore-{self.__hash__()} [Priority: {self.store_priority}]'

    def get_secret(self, key, default_value=None):
        raise NotImplementedError

    def set_secret(self, key, value):
        raise NotImplementedError

    def delete_secret(self, key):
        raise NotImplementedError

    def create_secret(self, name: str, length: int = 10) -> str:
        lower = string.ascii_lowercase
        upper = string.ascii_uppercase
        numbers = string.digits
        symbols = string.punctuation

        secret = random.sample(lower + upper + numbers + symbols, length)
        secret = "".join(secret)

        self.set_secret(key=name, value=secret)
        return secret


class SecretsStoreException(Exception):
    pass
