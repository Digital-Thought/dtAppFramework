import os
import sys
import subprocess
import logging
import re
import pybase64

from .secret_store import AbstractSecretStore, SecretsStoreException
from pykeepass import PyKeePass
from itertools import cycle
from ..misc import run_cmd


SECRETS_TEMPLATE = "A9mimmf7S7UBAAMAAhAAMcHy5r9xQ1C+WAUhavxa/wMEAAEAAAAEIAB+c18EHG1ACehtNrilCD7LKksuLKhpij3ASos" \
                   "MHKl6lAcQAPz8jH7mf3uXyGLdwSx+MIcFIACK+aJQP/TnUZ40xARPFdxoTGUjUrZaX9X+1sn88yJZTAYIAGDqAAAAAA" \
                   "AACCAAeJ2Q++y9lkMWc/j4D0v3xvmdKHM4m50HHNOgevyTmLkJIAAFlPtVDmmR3+GNNOKln1HpBWqNtbivBhRFgu2vZ" \
                   "aFUXAoEAAIAAAAABAANCg0KiqC+98/w+lY6h0JvDLUrNyiOmeC4Mk6l8oldUnVo3Yw/lvzzBUwbO+4e1BLVwFqrQDik" \
                   "ilEig94qJ35Db8myXC9Dym8St6giN+13CdeumHW35j077d5I24x48D3lpBtkTDNDfmwFS0gRRQk2LQbEQRtu15inWoJ" \
                   "n1YMre8+ysDrk/g5Ia/1FZLbzQx09SdGFVpf7MqlqmyqbIZR39vt0Z2x7UgfI3uXBdsIya+6UvlpZaWAxhRpwyK9efV" \
                   "1Arl/YsfPGCZpZyH3UHD3N+OKr79TALtakH5xg7cGL/qrAebTTI5uWG4z2t4IErdeimJoS74nHbzxXs1d5yNiOKIdMR" \
                   "Y+N1T8KXRat3XDAKHjq1aKhu+oetZ1jkTD3udoAJerH2a6WqKa6LvKAK+y2i926nkeF3uM8CHKrTGxCfpzlH4VqYEKs" \
                   "p72W3Lxsmj08eQH2AQmntO7frJhGSotNM4ogj9Adu3XowQ/fwuEGGKx27ItDbYC7CZUmUOTRokypPKsD1otxpziUdet" \
                   "w/g/gmzvcfS/OQWhSdr10G2+Dgb4366GHAQ846LRJA7qoo0o8+mWT+ObPLk1DLYir1Xf7Hg3gIUyYZgJS6R3u7NR9aC" \
                   "PiBmMoVbJjxSJWSHNCkzMxGoQ6RT522ilEok9Drtmb31ZPE+lF7bzulLxe2WAcJ2bYnZD3Nw1i1T+chi/hmk7Ej0UEB" \
                   "EWjxJYuutnXZvwLK6U0lLoAJvNhEXYEgSjC3sHgzKZrwpAy/bHTkAc+xDlXQFcO6FkZspuDWmv2GSgRtMXB0fC/WqSD" \
                   "JloyaUWRDKsThY2D7YJCdpIUjnFkO49DHY1yIEpDdR5xlg7OMQXcn71ZPk7kWzzTwfdSYAEWB+eWWSVh5BCz36URXyU" \
                   "FD1vZYCxDwy1rvmW6XzEVZrt4EJ0SRpj/zrnzFaWHG5vnIdGF5kmmJa36sekIix6QUExN0WPSi52PTDpA7eqYDAj3xW" \
                   "ElIZ87ihapGyqwoeALqCtRwaWUkUFa5aoPqeY5b9nPP5ZOaCPxXosO6AtDWtHRxVg5aQ3AoMQWGMT1Luo8WgmtNGl6M" \
                   "xlXjMlG19sidmYwISZI4MPH+GrFc/pI26GVffyxa134MFbdU/K75Q83dFSKnWanhs//Fqpda/sdH+bQQ1uZmkx/uWUk" \
                   "c6lyZe57unpJn2VWw0w5I9GYEpOD5y6IJQUQDMl2sRwMMszRfZnzTJWSbuk1cpPtUf/VM8JGn3mb0rpZTRi77FN8F6o" \
                   "EbBVvzfomSMNE+KgwpIDNSMXxQhxgowd4Cc5PQR5mferZgnnQKPFdwJnRuCUF3RD+JvTaKYaDWhOf2PTzNmm8EDf90V" \
                   "k6lMXGlpJM0Xf8QOg3QDFcgJh8H2qUaHstWbmCzom4rVfzs0WCjFVPJAjk7VVpa3I6DBhRYXlGRmf3zYxcJS2mDviPw" \
                   "jzxsakJWWTI4I2hdjlJ2oEXxnQNJpS/kcsI0/4M"

DEFAULT_PASSWORD = 'password'


class LocalSecretStore(AbstractSecretStore):

    def __init__(self, store_name, store_priority, root_store_path,
                 password: str = os.getenv('SECRETS_STORE_PASSWORD', None)) -> None:
        super().__init__(store_name, store_priority)
        self.store_path = os.path.join(root_store_path, "secrets.store.kdbx")

        if password is None:
            password = self.__guid()

        if not os.path.exists(self.store_path):
            self.__initialise_secrets_store(password)

        try:
            self.keepass_instance = PyKeePass(self.store_path, password)
        except Exception as ex:
            raise SecretsStoreException(f'Failed to open Secrets Store: {self.store_path}. Error: {str(ex)}')

        logging.info(f'Successfully opened Secrets Store: {self.store_path}')

    def __initialise_secrets_store(self, password):
        try:
            logging.info(f'Creating Secrets Store ({self.store_name}) at: {self.store_path}')
            with open(self.store_path, mode='wb') as kp_file:
                kp_file.write(pybase64.b64decode(SECRETS_TEMPLATE))

            keepass_instance = PyKeePass(self.store_path, DEFAULT_PASSWORD)
            keepass_instance.password = password
            keepass_instance.add_group(keepass_instance.root_group, self.store_name)
            keepass_instance.save()
            logging.info(f'Successfully created Secrets Store.')
        except Exception as ex:
            logging.error(f'Failed to create Secrets Store.  Error: {str(ex)}')
            raise ex

    def __store_group(self):
        return self.keepass_instance.find_groups(name=self.store_name, first=True)

    def __guid(self):
        base = None
        if sys.platform == 'darwin':
            base = run_cmd(
                "ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'")

        if sys.platform == 'win32' or sys.platform == 'cygwin' or sys.platform == 'msys':
            base = run_cmd('wmic csproduct get uuid').split('\n')[2] \
                .strip()

        if sys.platform.startswith('linux'):
            base = run_cmd('cat /var/lib/dbus/machine-id') or \
                   run_cmd('cat /etc/machine-id')

        if sys.platform.startswith('openbsd') or sys.platform.startswith('freebsd'):
            base = run_cmd('cat /etc/hostid') or \
                   run_cmd('kenv -q smbios.system.uuid')

        if not base:
            raise SecretsStoreException("Failed to determined unique machine ID")

        base += self.store_path
        key = re.sub("[^a-zA-Z]+", "", base)
        xored = ''.join(chr(ord(x) ^ ord(y)) for (x, y) in zip(base, cycle(key)))
        return pybase64.b64encode_as_string(xored.encode())

    def get_secret(self, key, default_value=None):
        entry = self.keepass_instance.find_entries(title=key, group=self.__store_group(), first=True)
        if not entry:
            return default_value
        return entry.password

    def set_secret(self, key, value):
        if self.get_secret(key):
            self.delete_secret(key)

        self.keepass_instance.add_entry(destination_group=self.__store_group(), title=key, username=key, password=value)
        self.__save()

    def delete_secret(self, key):
        entry = self.keepass_instance.find_entries(title=key, group=self.__store_group(), first=True)
        entry.delete()
        self.__save()

    def __save(self):
        self.keepass_instance.save()
        self.keepass_instance.reload()