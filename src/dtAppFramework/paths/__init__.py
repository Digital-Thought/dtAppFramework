import platform
import os
import shutil
import logging


class ApplicationPaths(object):

    def __init__(self, app_short_name, forced_os=None, forced_dev_mode=False, auto_create=True,
                 clean_temp=True) -> None:
        self.app_short_name = app_short_name
        self.forced_os = forced_os
        self.auto_create = auto_create
        self.clean_temp = clean_temp
        if forced_dev_mode:
            os.environ['DEV_MODE'] = "True"
        self.logging_root_path = self.__init_logging_root_path()
        self.app_data_root_path = self.__init_app_data_root_path()
        self.usr_data_root_path = self.__init_usr_data_root_path()
        self.tmp_root_path = self.__init_tmp_root_path()
        self.__init_directories()
        super().__init__()

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
            os.makedirs(self.app_data_root_path, exist_ok=True)
            os.makedirs(self.usr_data_root_path, exist_ok=True)
            os.makedirs(self.tmp_root_path, exist_ok=True)

    def __os(self):
        if self.forced_os:
            return self.forced_os
        else:
            return platform.system()

    def __init_logging_root_path(self):
        if os.environ.get("DEV_MODE", None):
            return f'{os.getcwd()}/logs'
        elif self.__os() == "Windows":
            return f'{os.environ.get("LOCALAPPDATA")}/{self.app_short_name}/logs'
        elif self.__os() == "Darwin":
            return f'{os.path.expanduser("~/Library/Logs")}/{self.app_short_name}'
        elif self.__os() == "Linux":
            return f'/var/log/{self.app_short_name}'

    def __init_app_data_root_path(self):
        if os.environ.get("DEV_MODE", None):
            return f'{os.getcwd()}/data/app'
        elif self.__os() == "Windows":
            return f'{os.environ.get("ALLUSERSPROFILE")}/{self.app_short_name}'
        elif self.__os() == "Darwin":
            return f'{os.path.expanduser("/Library/Application Support")}/{self.app_short_name}'
        elif self.__os() == "Linux":
            return f'/etc/{self.app_short_name}'

    def __init_usr_data_root_path(self):
        if os.environ.get("DEV_MODE", None):
            return f'{os.getcwd()}/data/usr'
        elif self.__os() == "Windows":
            return f'{os.environ.get("APPDATA")}/{self.app_short_name}'
        elif self.__os() == "Darwin":
            return f'{os.path.expanduser("~/Library/Application Support")}/{self.app_short_name}'
        elif self.__os() == "Linux":
            return f'{os.path.expanduser("~/.config")}/{self.app_short_name}'

    def __init_tmp_root_path(self):
        if os.environ.get("DEV_MODE", None):
            return f'{os.getcwd()}/temp'
        elif self.__os() == "Windows":
            return f'{os.environ.get("TEMP")}/{self.app_short_name}'
        elif self.__os() == "Darwin":
            return f'{os.environ.get("TMPDIR")}{self.app_short_name}'
        elif self.__os() == "Linux":
            return f'{os.path.expanduser("/tmp")}/{self.app_short_name}'
