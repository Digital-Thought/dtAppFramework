import logging
import logging.config
import os
import pathlib
import multiprocessing

from logging import Formatter

from datetime import datetime

import yaml
from colorlog import ColoredFormatter

from ..paths import ApplicationPaths
from ..settings import Settings
from .default_logging import default_config
from logging import Formatter

DEFAULT_FORMATTER = '%(log_color)s%(asctime)s - %(levelname)-8s - %(processName)s.%(process)d - %(threadName)s.%(thread)d - %(module)s.%(funcName)s.%(lineno)-3d - %(message)s%(reset)s'


def new_job():
    job_exists = True
    root_folder = os.environ['_dt_log_folder']
    job_id = 0
    while job_exists:
        job_id += 1
        job_exists = os.path.exists(f'{root_folder}/job-{job_id}')
        if job_exists:
            ctime = os.stat(f'{root_folder}/job-{job_id}').st_ctime
            now = datetime.now().timestamp()
            if (now - ctime) > 10:
                job_exists = True
            if (now - ctime) <= 10:
                job_exists = False

    return job_id


def get_logging_config(logging_source=None):
    application_paths = ApplicationPaths()
    config_path = None
    if logging_source:
        config_path = logging_source
    else:
        for _path in [os.path.join(application_paths.usr_data_root_path, "loggingConfig.yaml"),
                      os.path.join(application_paths.app_data_root_path, "loggingConfig.yaml"),
                      os.path.join(os.getcwd(), "config", "loggingConfig.yaml")]:
            if os.path.exists(_path):
                config_path = _path
                break

    if config_path:
        return config_path, yaml.safe_load(config_path)
    else:
        return "DEFAULT", default_config(log_level=Settings().get("logging.level", "INFO"))


def initialise_logging(spawned_process=False, redirect_console=False):
    app_paths = ApplicationPaths()
    if spawned_process:
        using_default = bool(os.environ['_dt_using_default'])
        logging_source = os.environ['_dt_logging_config_file']
        logging_source, logging_config = get_logging_config(logging_source)
    else:
        logging_source, logging_config = get_logging_config()
        os.environ['_dt_using_default'] = str(logging_source == "DEFAULT")
        os.environ['_dt_logging_config_file'] = logging_source
        using_default = logging_source == "DEFAULT"

    if using_default:
        if spawned_process:
            new_job()
            job_id = new_job()
            root_folder = os.environ['_dt_log_folder']
            log_folder = f'{root_folder}/job-{job_id}/{multiprocessing.current_process().name}'
        else:
            log_folder = f'{app_paths.logging_root_path}/{format(datetime.now().strftime("%Y%m%d_%H%M%S"))}'
            os.environ['_dt_log_folder'] = log_folder

        os.makedirs(log_folder, exist_ok=True)

        logging_config['handlers']['logfile_ALL']['filename'] = '{}/info-{}.log'.format(log_folder,
                                                                                        app_paths.app_short_name)
        logging_config['handlers']['logfile_ERR']['filename'] = '{}/error-{}.log'.format(log_folder,
                                                                                         app_paths.app_short_name)
        logging_config['handlers']['logfile_ELASTIC']['filename'] = '{}/elastic-{}.log'.format(log_folder,
                                                                                               app_paths.app_short_name)
        logging.config.dictConfig(logging_config)

        if not redirect_console:
            formatter = ColoredFormatter(DEFAULT_FORMATTER)

            console_stream = logging.StreamHandler()
            console_stream.setLevel(logging.DEBUG)
            console_stream.setFormatter(formatter)
            console_stream.name = 'console_ALL'

            logging.getLogger().addHandler(console_stream)
            logging.getLogger("defaultLogger").addHandler(console_stream)

            logging.getLogger('console').addHandler(console_stream)
            logging.getLogger('console').debug('Logging configuration read from: {}'.format(logging_source))

        return os.path.abspath(log_folder)

    else:
        logging.config.dictConfig(logging_config)
        logging.debug('Logging configuration read from: {}'.format(logging_source))
        return None