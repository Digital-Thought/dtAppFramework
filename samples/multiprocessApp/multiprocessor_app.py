import sys
import os
import logging
import time
from multiprocessing import Process, Queue


sys.path.append(os.path.abspath('../../src'))

from dtAppFramework import AbstractApp
from dtAppFramework import settings
from dtAppFramework import app_logging


num_of_procs = 10
queue_size = 100

def queue_processor(queue):
    logging.info(f"Running Queue Processing")
    while True:
        entry = queue.get()
        if entry is None:
            logging.warning(f"Queue Processing - COMPLETE")
            queue.put(None)
            break
        else:
            logging.info(f'Entry Value is {entry}')
            time.sleep(1)

class MultiProcessorApp(AbstractApp):

    def define_args(self, arg_parser):
        return

    def prepare_processors(self, queue, all_reader_procs):
        for x in range(0, num_of_procs):
            logging.info(f"Starting Queue Process: {str(x)}")
            reader_p = Process(target=queue_processor, args=(queue,))
            reader_p.start()
            all_reader_procs.append(reader_p)

    def load_queue(self, queue):
        logging.info(f"Running Queue Loader")
        for x in range(0, queue_size):
            queue.put(x)
        queue.put(None)

    def main(self, args):
        queue = Queue()
        all_reader_procs = list()
        self.prepare_processors(queue, all_reader_procs)
        self.load_queue(queue)

        for proc in all_reader_procs:
            proc.join()
        time.sleep(10)
        queue = Queue()
        all_reader_procs = list()
        self.prepare_processors(queue, all_reader_procs)
        self.load_queue(queue)

        for proc in all_reader_procs:
            proc.join()


os.environ['DEV_MODE'] = "True"
MultiProcessorApp(description="MultiProcessor App showing paths in Dev Mode", version="1.0", short_name="multiprocessor_dev_app",
             full_name="MultiProcessor Development Application").run()
