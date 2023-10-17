import sys
import os
import time

sys.path.append(os.path.abspath('../../src'))

from dtAppFramework.app import AbstractApp
from dtAppFramework import settings
from dtAppFramework.secrets_store import SecretsManagerScopePriorities


class SimpleDevApp(AbstractApp):

    def define_args(self, arg_parser):
        return

    def main(self, args):
        print("Main Called")
        print(self.secrets_manager.get_secret('AWS_Secret#SEC01/SecretsManager/Utilities', 'NOPE', scope=SecretsManagerScopePriorities.AWS))
        print(self.application_settings.get("setting.test"))


if __name__ == "__main__":
    os.environ['DEV_MODE'] = "True"
    SimpleDevApp(description="Simple AWS Secrets App showing paths in Dev Mode", version="1.0", short_name="aws_secrets_app",
                 full_name="Simple Development Application", console_app=True).run()
