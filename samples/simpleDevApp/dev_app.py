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
        print(self.secrets_manager.set_secret('setting', 'NOPE'))
        print(self.secrets_manager.get_secret('setting', None))
        print(self.secrets_manager.set_secret('setting4', 'App Secret', scope=SecretsManagerScopePriorities.APP))
        print(self.secrets_manager.get_secret('setting4', 'Checked from Default', scope=SecretsManagerScopePriorities.USER))
        print(self.secrets_manager.get_secret('setting4', 'Checked from App', scope=SecretsManagerScopePriorities.APP))
        # self.settings['setting2'] = 'Persistent Value - Overwrite App'
        time.sleep(20)


if __name__ == "__main__":
    os.environ['DEV_MODE'] = "True"
    SimpleDevApp(description="Simple App showing paths in Dev Mode", version="1.0", short_name="simple_dev_app",
                 full_name="Simple Development Application", console_app=True).run()
