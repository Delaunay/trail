from argparse import Namespace
from typing import Callable

from track.containers.types import float32
from track.structure import Trial, Status

from track.utils.signal import SignalHandler

from track.aggregators.aggregator import Aggregator
from track.aggregators.aggregator import RingAggregator
from track.aggregators.aggregator import StatAggregator
from track.aggregators.aggregator import TimeSeriesAggregator
from track.aggregators.aggregator import ValueAggregator
from track.persistence.protocol import Protocol
from track.chrono import ChronoContext

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


def _make_container(step, aggregator):
    if step is None:
        if aggregator is None:
            # favor ts aggregator because it has an option to cut the TS for printing purposes
            return ts_aggregator()
        return aggregator()
    else:
        return dict()


class LoggerChronoContext:
    def __init__(self, protocol, trial, acc=StatAggregator(), name=None, **kwargs):
        self.chrono = ChronoContext(acc=acc)
        self.protocol = protocol
        self.trial = trial
        self.args = kwargs
        self.name = name

    def __enter__(self):
        v = self.chrono.__enter__()
        if self.name is None:
            self.protocol.log_trial_start(self.trial)
        else:
            self.protocol.log_trial_chrono_start(self.trial, self.name, **self.args)
        return v

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.name is None:
            self.protocol.log_trial_finish(self.trial, exc_type, exc_val, exc_tb)
        else:
            self.protocol.log_trial_chrono_finish(self.trial, self.name, exc_type, exc_val, exc_tb)

        return self.chrono.__exit__(exc_type, exc_val, exc_tb)


class TrialLogger:
    """ Unified logger interface.
    To log to a specific backend you should pass the desired backend to the constructor """

    def __init__(self, trial: Trial, protocol: Protocol):
        self.protocol = protocol
        self.trial = trial

        acc = ValueAggregator()
        self.chronos = dict(runtime=acc)

        self.parent_chrono = LoggerChronoContext(self.protocol, self.trial, acc=acc)
        self.signal_handler = LogSignalHandler(self)

    def add_tag(self, key, value):
        self.trial.tags[key] = value

    def log_arguments(self, args: Namespace = None, **kwargs):
        if args is not None:
            kwargs.update(dict(**vars(args)))

        self.protocol.log_trial_arguments(self.trial, **kwargs)

    def log_metrics(self, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        self.protocol.log_trial_metrics(self.trial, step, aggregator, **kwargs)

    def log_metadata(self, aggregator: Callable[[], Aggregator] = None, **kwargs):
        self.protocol.log_trial_metadata(self.trial, aggregator, **kwargs)

    def add_tags(self, **kwargs):
        self.protocol.add_trial_tags(self.trial, **kwargs)

    def chrono(self, name: str, aggregator: Callable[[], Aggregator] = stat_aggregator,
               start_callback=None,
               end_callback=None):

        return LoggerChronoContext(
            self.protocol,
            self.trial,
            acc=aggregator(),
            name=name,
            aggregator=aggregator,
            start_callback=start_callback,
            end_callback=end_callback)

    # Context API for starting the top level chrono
    def finish(self, exc_type=None, exc_val=None, exc_tb=None):
        if exc_type is not None:
            self.protocol.set_trial_status(self.trial, Status.Exception, error=exc_type)
        else:
            self.protocol.set_trial_status(self.trial, Status.Completed)

        self.parent_chrono.__exit__(exc_type, exc_val, exc_tb)
        if exc_type is not None:
            raise exc_type

    def start(self):
        self.set_status(Status.Running)
        self.parent_chrono.__enter__()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish(exc_type, exc_val, exc_tb)

    def set_status(self, status, error=None):
        self.protocol.set_trial_status(self.trial, status, error)

    def log_file(self, file_name):
        pass

    def log_directory(self, name, recursive=False):
        pass

    def set_project(self, project):
        pass

    def set_group(self, group):
        pass


