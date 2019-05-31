import signal
import sys


class SignalHandler:
    def __init__(self):
        signal.signal(signal.SIGINT, self._sigint)
        signal.signal(signal.SIGTERM, self._sigterm)

    def _sigterm(self, signum, frame):
        self.sigterm(signum, frame)
        sys.exit(1)

    def _sigint(self, signum, frame):
        self.sigint(signum, frame)
        sys.exit(1)

    def sigterm(self, signum, frame):
        raise NotImplementedError()

    def sigint(self, signum, frame):
        raise NotImplementedError()
