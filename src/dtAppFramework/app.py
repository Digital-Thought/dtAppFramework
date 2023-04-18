import argparse
import logging
import os
import sys

import psutil
import traceback

from multiprocessing import current_process
from argparse import ArgumentParser
from contextlib import redirect_stdout, redirect_stderr
from . import app_logging
from . import paths
from . import settings
from . import secrets_store
from . import resources


class AbstractApp(object):

    def __init__(self, description=None, version=None, short_name=None, full_name=None, console_app=True) -> None:
        self.app_spec = {
            'description': description,
            'version': version,
            'short_name': short_name,
            'full_name': full_name
        }
        for key in self.app_spec:
            if not self.app_spec[key]:
                raise Exception(f"Missing '{key}'")
        self.console_app = console_app
        self.application_paths = None
        self.application_settings = None
        self.secrets_manager = None
        self.resource_manager = None
        self.log_path = None
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
        if not self.is_multiprocess_spawned_instance():
            self.application_paths.log_paths()

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
        else:
            arg_parser.add_argument('--password', action='store', type=str,
                                    required=False, help="Secrets Store password")

            self.define_args(arg_parser)

    def __add_secret__(self, args):
        try:
            self.secrets_manager.set_secret(args.name, args.value)
        except Exception as ex:
            logging.error(f'Error occurred while adding secret {args.name}.  Error: {str(ex)}')
            raise ex

    def __initialise_singletons(self):
        self.application_paths = paths.ApplicationPaths(app_short_name=self.app_spec['short_name'],
                                                        spawned_instance=self.is_multiprocess_spawned_instance())
        self.application_settings = settings.Settings(application_paths=self.application_paths)
        self.secrets_manager = secrets_store.SecretsManager(application_paths=self.application_paths,
                                                            application_settings=self.application_settings)
        self.resource_manager = resources.ResourceManager(application_paths=self.application_paths)

    def run(self):
        try:
            arg_parser = argparse.ArgumentParser(prog=self.app_spec["short_name"], description=self.app_spec["description"])
            self.__define_args(arg_parser)
            self.__initialise_singletons()
            self.log_path = app_logging.initialise_logging(spawned_process=self.is_multiprocess_spawned_instance(),
                                                           redirect_console=not self.console_app)
            stdout_txt_file = None
            stderr_txt_file = None

            if not self.console_app:
                stdout_txt = '{}/stdout.txt'.format(self.log_path, self.application_paths.app_short_name)
                stderr_txt = '{}/stderr.txt'.format(self.log_path, self.application_paths.app_short_name)

                stdout_txt_file = open(stdout_txt, mode='w', buffering=1)
                stderr_txt_file = open(stderr_txt, mode='w', buffering=1)
                sys.stdout = stdout_txt_file
                sys.stderr = stderr_txt_file

            if not self.is_multiprocess_spawned_instance():
                header_message = f'{self.app_spec["full_name"]} ({self.app_spec["short_name"]}), ' \
                                 f'Version: {self.app_spec["version"]}. Process ID: {os.getpid()}'
                logging.info(header_message)
                print(header_message)
                if self.log_path is not None:
                    print(f'Log Path: {self.log_path}')
                print('\n')
            else:
                header_message = f'SPAWNED PROCESS --- {self.app_spec["full_name"]} ({self.app_spec["short_name"]}), ' \
                                 f'Version: {self.app_spec["version"]}. '
                logging.info(header_message)
                print(header_message)

            args = arg_parser.parse_args()

            if not self.is_multiprocess_spawned_instance():
                if args.add_secret:
                    self.__add_secret__(args)
                else:
                    self.__main(args)
            else:
                self.load_config(args)
        except KeyboardInterrupt as kbi:
            logging.warning('(KeyboardInterrupt) Exiting application.')
            if not self.console_app:
                stdout_txt_file.close()
                stderr_txt_file.close()
