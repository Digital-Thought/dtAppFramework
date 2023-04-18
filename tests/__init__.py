import sys
import os
import logging

sys.path.append(os.path.abspath('./src'))

from dtAppFramework.paths import ApplicationPaths
from dtAppFramework.secrets_store import SecretsManager
from dtAppFramework import app_logging


os.environ['DEV_MODE'] = "True"

paths = ApplicationPaths(app_short_name="unit_test")
secrets_manager = SecretsManager()
app_logging.initialise_logging()
paths.log_paths()
logging.info("hello")