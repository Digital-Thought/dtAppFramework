import platform
import os
import shutil
import logging

from multiprocessing import current_process
from ..misc import singleton


@singleton()
class ApplicationPaths(object):

    def __init__(self, app_short_name, forced_os=None, forced_dev_mode=False, auto_create=True,
                 clean_temp=True, spawned_instance=False, *args, **kwargs) -> None:
        super().__init__()
        self.app_short_name = app_short_name
        self.forced_os = forced_os
        self.spawned_instance = spawned_instance
        self.auto_create = auto_create
        self.clean_temp = clean_temp
        self.forced_dev_mode = forced_dev_mode

        if self.forced_dev_mode:
            os.environ['DEV_MODE'] = "True"

        self.logging_root_path = self.__init_logging_root_path()
        self.app_data_root_path = self.__init_app_data_root_path()
        self.usr_data_root_path = self.__init_usr_data_root_path()
        self.tmp_root_path = self.__init_tmp_root_path()

        self.__init_directories()

    def log_paths(self):
        logging.info(f'Logging Root Path: {self.logging_root_path}')
        logging.info(f'Application Data Root Path: {self.app_data_root_path}')
        logging.info(f'User Data Root Path: {self.usr_data_root_path}')
        logging.info(f'Temp Root Path: {self.tmp_root_path}')

    def __init_directories(self):
        if self.clean_temp and os.path.exists(self.tmp_root_path):
            shutil.rmtree(self.tmp_root_path, ignore_errors=False)

        if self.auto_create:
            os.makedirs(self.tmp_root_path, exist_ok=True)
            os.makedirs(self.logging_root_path, exist_ok=True)
            os.makedirs(self.usr_data_root_path, exist_ok=True)

            try:
                os.makedirs(self.app_data_root_path, exist_ok=True)
            except Exception as ex:
                print(f'Skipping creation of application data path {self.app_data_root_path}. {ex}')

    def __os(self):
        if self.forced_os:
            return self.forced_os
        else:
            return platform.system()

    def __init_logging_root_path(self):
        _path = None
        if os.environ.get("DEV_MODE", None):
            _path = f'{os.getcwd()}/logs'
        elif self.__os() == "Windows":
            _path = f'{os.environ.get("LOCALAPPDATA")}/{self.app_short_name}/logs'
        elif self.__os() == "Darwin":
            _path = f'{os.path.expanduser("~/Library/Logs")}/{self.app_short_name}'
        elif self.__os() == "Linux":
            _path = f'/var/log/{self.app_short_name}'

        os.environ['dt_LOGGING_PATH'] = _path
        return _path

    def __init_app_data_root_path(self):
        _path = None
        if os.environ.get("DEV_MODE", None):
            _path = f'{os.getcwd()}/data/app'
        elif self.__os() == "Windows":
            _path = f'{os.environ.get("ALLUSERSPROFILE")}/{self.app_short_name}'
        elif self.__os() == "Darwin":
            _path = f'{os.path.expanduser("/Library/Application Support")}/{self.app_short_name}'
        elif self.__os() == "Linux":
            _path = f'/etc/{self.app_short_name}'

        os.environ['dt_APP_DATA'] = _path
        return _path

    def __init_usr_data_root_path(self):
        _path = None
        if os.environ.get("DEV_MODE", None):
            _path = f'{os.getcwd()}/data/usr'
        elif self.__os() == "Windows":
            _path = f'{os.environ.get("APPDATA")}/{self.app_short_name}'
        elif self.__os() == "Darwin":
            _path = f'{os.path.expanduser("~/Library/Application Support")}/{self.app_short_name}'
        elif self.__os() == "Linux":
            _path = f'{os.path.expanduser("~/.config")}/{self.app_short_name}'

        os.environ['dt_USR_DATA'] = _path
        return _path

    def __init_tmp_root_path(self):
        _path = None
        if self.spawned_instance:
            _path = f'{os.environ["dt_TMP"]}/{current_process().name}'
        elif os.environ.get("DEV_MODE", None):
            _path = f'{os.getcwd()}/temp'
        elif self.__os() == "Windows":
            _path = f'{os.environ.get("TEMP")}/{self.app_short_name}'
        elif self.__os() == "Darwin":
            _path = f'{os.environ.get("TMPDIR")}{self.app_short_name}'
        elif self.__os() == "Linux":
            _path = f'{os.path.expanduser("/tmp")}/{self.app_short_name}'

        os.environ['dt_TMP'] = _path
        return _path
