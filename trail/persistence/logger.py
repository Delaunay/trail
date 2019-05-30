from argparse import Namespace


class LoggerBackend:

    def log_argument(self, k, v):
        raise NotImplementedError()

    def log_arguments(self, args: Namespace):
        raise NotImplementedError()

    def log_metrics(self, step=None, **kwargs):
        raise NotImplementedError()


class NoLogLogger(LoggerBackend):

    def log_argument(self, k, v):
        pass

    def log_arguments(self, args: Namespace):
        pass

    def log_metrics(self, step=None, **kwargs):
        pass
