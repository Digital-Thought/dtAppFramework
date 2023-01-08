import sys
import os

sys.path.append(os.path.abspath('../../src'))

from dtAppFramework import AbstractApp
from dtAppFramework import settings


class SimpleDevApp(AbstractApp):

    def define_args(self, arg_parser):
        return

    def main(self, args):
        print("Main Called")
        print(self.settings['setting'])
        print(self.settings['setting1'])
        print(self.settings['setting2'])
        print(self.settings.get('setting3', None))
        self.settings['setting2'] = 'Persistent Value - Overwrite App'


if __name__ == "__main__":
    os.environ['DEV_MODE'] = "True"
    SimpleDevApp(description="Simple App showing paths in Dev Mode", version="1.0", short_name="simple_dev_app",
                 full_name="Simple Development Application").run()
