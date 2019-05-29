

class Logger:
    def log_metric(self, k, v):
        raise NotImplementedError()

    def chrono(self):
        raise NotImplementedError()


