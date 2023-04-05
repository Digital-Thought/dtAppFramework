from ..paths import ApplicationPaths

import os
import logging


class ResourceManager(object):

    def __init__(self, app_paths: ApplicationPaths) -> None:
        super().__init__()
        self.app_paths = app_paths
        self.resource_paths = self.__load_default_paths__()

    def __load_default_paths__(self):
        return [os.path.join(self.app_paths.usr_data_root_path, "_resources"),
                os.path.join(self.app_paths.app_data_root_path, "_resources"), os.path.join(os.getcwd(), "_resources")]

    def add_resource_path(self, path):
        self.resource_paths.append(path)

    def remove_resource_path(self, path):
        self.resource_paths.remove(path)

    def get_resource_path(self, resource):
        for path in self.resource_paths:
            if os.path.exists(os.path.join(path, resource)):
                logging.info(f'Returning resource from: "{os.path.join(path, resource)}"')
                return os.path.join(path, resource)

        logging.error(f'Resource: "{resource}" could not be found')
        return None
