import logging
import logging.config
import os
import pathlib
import multiprocessing

from datetime import datetime

import yaml
from colorlog import ColoredFormatter

from ..paths import ApplicationPaths

logging_resource_folder = "{}/../_resources".format(str(pathlib.Path(__file__).parent.absolute()))
default_logging_configuration_file = f'{logging_resource_folder}/default_config.yaml'
logging_configuration_file = './config/loggingConfig.yaml'

DEFAULT_FORMATTER = '%(log_color)s%(asctime)s - %(levelname)-8s - %(processName)s.%(process)d - %(threadName)s.%(thread)d - %(module)s.%(funcName)s.%(lineno)-3d - %(message)s%(reset)s'
DEFAULT_ELASTIC_FORMATTER = 'ELASTIC: %(log_color)s%(asctime)s - %(levelname)-8s - %(processName)s.%(process)d - %(threadName)s.%(thread)d - %(module)s.%(funcName)s.%(lineno)-3d - %(message)s%(reset)s'


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


def init(app_name, app_paths: ApplicationPaths, configuration_file: str = None, spawned_process=False):
    if configuration_file and not os.path.exists(configuration_file):
        raise FileNotFoundError(f'Missing specified logging configuration file: {configuration_file}')

    using_default = False
    if spawned_process:
        using_default = bool(os.environ['_dt_using_default'])
        logging_config_file = os.environ['_dt_logging_config_file']
    else:
        if configuration_file and os.path.exists(configuration_file):
            logging_config_file = configuration_file
        elif os.path.exists(logging_configuration_file):
            logging_config_file = logging_configuration_file
        else:
            logging_config_file = default_logging_configuration_file
            using_default = True

        os.environ['_dt_using_default'] = str(using_default)
        os.environ['_dt_logging_config_file'] = logging_config_file

    with open(logging_config_file, 'r') as config_file:
        logging_config = yaml.safe_load(config_file)

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

        formatter = ColoredFormatter(DEFAULT_FORMATTER)

        console_stream = logging.StreamHandler()
        console_stream.setLevel(logging.DEBUG)
        console_stream.setFormatter(formatter)
        console_stream.name = 'console_ALL'

        logging_config['handlers']['logfile_ALL']['filename'] = '{}/info-{}.log'.format(log_folder, app_name)
        logging_config['handlers']['logfile_ERR']['filename'] = '{}/error-{}.log'.format(log_folder, app_name)
        logging_config['handlers']['logfile_ELASTIC']['filename'] = '{}/elastic-{}.log'.format(log_folder, app_name)
        logging.config.dictConfig(logging_config)
        logging.getLogger().addHandler(console_stream)
        logging.getLogger("defaultLogger").addHandler(console_stream)

        logging.getLogger('console').addHandler(console_stream)
        logging.getLogger('console').debug('Logging configuration read from: {}'.format(logging_config_file))

        return os.path.abspath(log_folder)

    else:
        logging.config.dictConfig(logging_config)
        logging.debug('Logging configuration read from: {}'.format(logging_config_file))

        return None
