import signal


class SignalHandler:
    def __init__(self):
        signal.signal(signal.SIGINT, self.sigint)
        signal.signal(signal.SIGTERM, self.sigterm)

    def sigterm(self, signum, frame):
        raise NotImplementedError()

    def sigint(self, signum, frame):
        raise NotImplementedError()
