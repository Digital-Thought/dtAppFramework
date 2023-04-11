import sys
import os

sys.path.append(os.path.abspath('../../src'))

from dtAppFramework.paths import ApplicationPaths

os.environ['DEV_MODE'] = "True"
app_paths = ApplicationPaths(app_short_name="test")
app_paths2 = ApplicationPaths()

print(app_paths is app_paths2)