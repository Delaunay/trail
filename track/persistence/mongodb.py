from .logger import LoggerBackend
from pymongo import MongoClient
from argparse import Namespace


class MongoDbLogger(LoggerBackend):
    def __init__(self, address):
        self.client = MongoClient(address)

    def log_argument(self, k, v):
        pass

    def log_arguments(self, args: Namespace):
        pass

    def log_metrics(self, step=None, **kwargs):
        pass

    def set_status(self, status, error=None):
        pass

    def log_others(self, **kwargs):
        pass

