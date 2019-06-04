from argparse import Namespace
from typing import Callable

from trail.containers.types import float32
from trail.struct import Trial, Status

from trail.utils.signal import SignalHandler

from trail.chrono import ChronoContext
from trail.aggregators.aggregator import Aggregator
from trail.aggregators.aggregator import RingAggregator
from trail.aggregators.aggregator import StatAggregator
from trail.aggregators.aggregator import ValueAggregator
from trail.aggregators.aggregator import TimeSeriesAggregator
from trail.persistence.logger import LoggerBackend, NoLogLogger


ring_aggregator = RingAggregator.lazy(10, float32)
stat_aggregator = StatAggregator.lazy(1)
ts_aggregator = TimeSeriesAggregator.lazy()


class LogSignalHandler(SignalHandler):
    def __init__(self, logger):
        super(LogSignalHandler, self).__init__()
        self.logger = logger

    def sigterm(self, signum, frame):
        self.logger.set_status(Status.Interrupted, error=frame)

    def sigint(self, signum, frame):
        self.logger.set_status(Status.Interrupted, error=frame)


class Logger(LoggerBackend):
    """ Unified logger interface.
    To log to a specific backend you should pass the desired backend to the constructor """

    def __init__(self, trial: Trial, backend=NoLogLogger()):
        self.backend = backend
        self.trial = trial
        acc = ValueAggregator()
        self.depth = 0
        self.trial.chronos['runtime'] = acc
        self.parent_chrono = ChronoContext('runtime', acc, None, self)
        self.start()
        self.signal_handler = LogSignalHandler(self)

    def add_tag(self, key, value):
        self.trial.tags[key] = value

    def log_argument(self, key, value):
        self.trial.parameters[key] = value
        self.backend.log_argument(key, value)

    def log_arguments(self, args: Namespace):
        self.trial.parameters.update(dict(**vars(args)))
        self.backend.log_arguments(args)

    def _make_container(self, step, aggregator):
        if step is None:
            if aggregator is None:
                # favor ts aggregator because it has an option to cut the TS for printing purposes
                return ts_aggregator()
            return aggregator()
        else:
            return dict()

    def log_metrics(self, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        """
            :params step optional key that optionally can be set; originally meant as a way to specify a kind of
                    id representing at which step of the training process the model is at.

            :params aggregator: custom container used to store the metrics. if not specified it will fall back
                    to standard `list` and `dict`

            :params kwargs: key, value pair representing the metrics that need to be logged
        """
        for k, v in kwargs.items():
            container = self.trial.metrics.get(k)

            if container is None:
                container = self._make_container(step, aggregator)
                self.trial.metrics[k] = container

            if step is not None and isinstance(container, dict):
                container[step] = v
            elif step:
                container.append((step, v))
            else:
                container.append(v)

        self.backend.log_metrics(step, **kwargs)

    def log_metadata(self, aggregator: Callable[[], Aggregator] = None, **kwargs):
        for k, v in kwargs.items():
            container = self.trial.metadata.get(k)

            if container is None:
                container = self._make_container(None, aggregator)
                self.trial.metadata[k] = container

            container.append(v)

        self.backend.log_metadata(**kwargs)

    def chrono(self, name: str, aggregator: Callable[[], Aggregator] = stat_aggregator, sync=None):
        """ create a chrono context to time the runtime of the code inside it"""
        agg = self.trial.chronos.get(name)
        if agg is None:
            agg = aggregator()
            self.trial.chronos[name] = agg

        return ChronoContext(name, agg, sync, self.parent_chrono)

    # Context API for starting the top level chrono
    def finish(self, exc_type=None, exc_val=None, exc_tb=None):
        metrics = {}
        for k, v in self.trial.chronos.items():
            metrics[f'chrono_{k}'] = v.to_json()

        self.backend.log_metadata(**metrics)
        if exc_type is not None:
            self.set_status(Status.Exception, error=exc_type)
        else:
            self.set_status(Status.Completed)

        self.parent_chrono.__exit__(exc_type, exc_val, exc_tb)

    def start(self):
        self.set_status(Status.Running)
        self.parent_chrono.__enter__()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish(exc_type, exc_val, exc_tb)

    def set_status(self, status, error=None):
        self.trial.status = status
        if error is not None:
            self.trial.errors.append(error)
        self.backend.set_status(status, error)

    def log_file(self, file_name):
        pass

    def log_directory(self, name, recursive=False):
        pass

    def set_project(self, project):
        pass

    def set_group(self, group):
        raise NotImplementedError()


