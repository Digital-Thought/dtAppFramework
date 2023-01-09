import argparse
import logging
import os
import psutil
import traceback

from multiprocessing import current_process
from argparse import ArgumentParser
from . import app_logging
from .paths import ApplicationPaths
from . import settings
from . import secrets_store


class AbstractApp(object):

    def __init__(self, description=None, version=None, short_name=None, full_name=None) -> None:
        self.app_spec = {
            'description': description,
            'version': version,
            'short_name': short_name,
            'full_name': full_name
        }
        for key in self.app_spec:
            if not self.app_spec[key]:
                raise Exception(f"Missing '{key}'")
        self.app_paths = ApplicationPaths(app_short_name=self.app_spec['short_name'])
        self.log_path = None
        self.settings = None
        super().__init__()

    def version(self) -> str:
        return self.app_spec["version"]

    def define_args(self, arg_parser: ArgumentParser):
        raise NotImplementedError

    def is_multiprocess_spawned_instance(self):
        return current_process().name != "MainProcess"

    def main(self, args):
        raise NotImplementedError

    def load_config(self, args):
        settings.load(self.app_paths)

        if args.password:
            secrets_store.get_secret_store(app_paths=self.app_paths, password=args.password)
        else:
            secrets_store.get_secret_store(app_paths=self.app_paths)

        self.settings = settings.config
        if not self.is_multiprocess_spawned_instance():
            self.app_paths.log_paths()

    def __main(self, args):
        self.load_config(args)
        self.main(args)

    def __define_args(self, arg_parser: ArgumentParser):
        arg_parser.add_argument('--init', action='store_true', required=False, help='Initialise environment')
        arg_parser.add_argument('--add_secret', action='store_true', required=False, help='Add secret to store')
        arg_parser.add_argument('--run', action='store_true', required=False, help='Run Processor')

        opts, rem_args = arg_parser.parse_known_args()

        if opts.init:
            arg_parser.add_argument('--password', action='store', type=str, required=False,
                                    help="Secrets Store password")

        elif opts.add_secret:
            arg_parser.add_argument('--password', action='store', type=str, required=False,
                                    help="Secrets Store password")
            arg_parser.add_argument('--name', action='store', type=str, required=True, help="Secret Name")
            arg_parser.add_argument('--value', action='store', type=str, required=True, help="Secret Value")
            arg_parser.add_argument('--env', action='store_true',
                                    help="Load secret as environment variable on Secrets Store initialisation")
        else:
            arg_parser.add_argument('--password', action='store', type=str,
                                    required=False, help="Secrets Store password")

            self.define_args(arg_parser)

    def __initialise_environment__(self, args):
        try:
            if args.password:
                secrets_store.initialise_new_secrets_store(app_paths=self.app_paths, password=args.password)
            else:
                secrets_store.initialise_new_secrets_store(app_paths=self.app_paths)
        except Exception as ex:
            logging.error(f'Failed to create Secrets Store.  Error: {str(ex)}')
            raise ex

    def __add_secret__(self, args):
        try:
            if args.password:
                store = secrets_store.get_secret_store(app_paths=self.app_paths, password=args.password)
            else:
                store = secrets_store.get_secret_store(app_paths=self.app_paths)

            store.add_secret(args.name, args.value, args.env)
            store.close()
        except Exception as ex:
            logging.error(f'Error occurred while adding secret {args.name}.  Error: {str(ex)}')
            raise ex

    def run(self):
        arg_parser = argparse.ArgumentParser(prog=self.app_spec["short_name"], description=self.app_spec["description"])
        self.__define_args(arg_parser)

        self.log_path = app_logging.init(self.app_spec["short_name"], app_paths=self.app_paths,
                                         spawned_process=self.is_multiprocess_spawned_instance())

        if not self.is_multiprocess_spawned_instance():
            logging.info(
                f'{self.app_spec["full_name"]} ({self.app_spec["short_name"]}), Version: {self.app_spec["version"]}. '
                f'Process ID: {os.getpid()}')
            print(f'Version: {self.app_spec["version"]}')
            if self.log_path is not None:
                print(f'Log Path: {self.log_path}')
            print('\n')
        else:
            logging.info(
                f'SPAWNED PROCESS --- {self.app_spec["full_name"]} ({self.app_spec["short_name"]}), Version: {self.app_spec["version"]}. '
                f'Process ID: {os.getpid()}')

        args = arg_parser.parse_args()

        if not self.is_multiprocess_spawned_instance():
            if args.init:
                self.__initialise_environment__(args)
            elif args.add_secret:
                self.__add_secret__(args)
            else:
                self.__main(args)
        else:
            self.load_config(args)
