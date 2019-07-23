import inspect
from typing import Callable

from track.utils.stat import StatStream

from track.configuration import options
from track.containers.types import float32
from track.structure import Trial, Status
from track.aggregators.aggregator import Aggregator
from track.aggregators.aggregator import RingAggregator
from track.aggregators.aggregator import StatAggregator
from track.aggregators.aggregator import TimeSeriesAggregator
from track.aggregators.aggregator import ValueAggregator
from track.persistence.protocol import Protocol
from track.chrono import ChronoContext
from track.utils.delay import is_delayed_call
from track.utils.signal import SignalHandler
from track.utils.throttle import throttled
from track.utils.eta import EstimatedTime
from track.utils.out import RingOutputDecorator

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

    def atexit(self):
        if self.logger.has_started and not self.logger.has_finished:
            self.logger.set_status(Status.Completed)


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
    """Unified logger interface. This object should be created through the `TrackClient` interface

    Parameters
    ----------
    trial: Trial
        the trial that the logger modifies

    protocol: Protocol
        the storage protocol used to persist the log calls
    """

    def __init__(self, trial: Trial, protocol: Protocol):
        self.protocol = protocol
        self.trial = trial

        acc = ValueAggregator()
        self.chronos = dict(runtime=acc)
        self.eta = EstimatedTime(None, 1)
        self.batch_printer = None

        self.parent_chrono = LoggerChronoContext(self.protocol, self.trial, acc=acc)
        self.signal_handler = LogSignalHandler(self)
        self.has_finished = False
        self.has_started = False
        self.code = None
        self.stdout = None
        self.stderr = None

    def log_arguments(self, **kwargs):
        """log the trial arguments. This function has not effect if the trial was already created."""
        # arguments are set at trial creation
        if is_delayed_call(self.trial):
            self.trial = self.trial(arguments=kwargs)

    def log_metrics(self, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        """insert metrics values inside a trial

        Parameters
        ----------
        step: any
            a value representing a training step (could be epoch, timestamp, ...)

        kwargs:
            dictionary of metrics (metric_name: value)

        aggregator: Optional[Callable[[], Aggregator]]
            how to store the values locally
        """
        # this in case the user is not using the context API.
        # this means our runtime info might be a bit optimistic
        # but for long training period it should not matter too much
        if not self.has_started:
            self.start()

        self.protocol.log_trial_metrics(self.trial, step, aggregator, **kwargs)

    def log_metadata(self, aggregator: Callable[[], Aggregator] = None, **kwargs):
        """insert metadata value inside a trial

        Parameters
        ----------
        kwargs:
            dictionary of metrics (metadata_name: value)
        """
        self.protocol.log_trial_metadata(self.trial, aggregator, **kwargs)

    def add_tags(self, **kwargs):
        self.protocol.add_trial_tags(self.trial, **kwargs)

    def chrono(self, name: str, aggregator: Callable[[], Aggregator] = stat_aggregator,
               start_callback=None,
               end_callback=None):
        """Start a chronometer to measure the time spent in that block

        Parameters
        ----------
        name: str
            name of the timer

        aggregator:
            how to save the values, by default it uses the `StatAggregator` and only the mean, sd, max, min values are
            kept once the training is done

        start_callback: Callable
            function that is called once the timer starts

        end_callback: Callable
            function that is called once the timer ends

        Returns
        -------
        returns a context manager that represents the timer
        """

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
        self.has_finished = True

        if exc_type is not None:
            self.protocol.set_trial_status(self.trial, Status.Exception, error=exc_type)
        # in some cases we build the trial ahead of time so finish my be called
        # while the trial has not started yet.
        elif self.has_started:
            self.protocol.set_trial_status(self.trial, Status.Completed)

            self.parent_chrono.__exit__(exc_type, exc_val, exc_tb)
            if exc_type is not None:
                raise exc_type

    def start(self):
        self.has_started = True
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

    def log_code(self):
        self.code = open(inspect.stack()[-1].filename, 'r').read()
        return self

    def capture_output(self, output_size=50):
        import sys
        do_stderr = sys.stderr is not sys.stdout

        self.stdout = RingOutputDecorator(file=sys.stdout, n_entries=options('log.stdout_capture', output_size))
        sys.stdout = self.stdout

        if do_stderr:
            self.stderr = RingOutputDecorator(file=sys.stderr, n_entries=options('log.stderr_capture', output_size))
            sys.stderr = self.stderr
        return self

    def set_eta_total(self, t):
        self.eta.set_totals(t)
        return self

    def show_eta(self, step: int, timer: StatStream, msg: str = '',
                 throttle=options('log.print.throttle', None),
                 every=options('log.print.every', None),
                 no_print=options('log.print.disable', False)):

        self.eta.timer = timer

        if self.batch_printer is None:
            self.batch_printer = throttled(self.eta.show_eta, throttle, every)

        if not no_print:
            self.batch_printer(step, msg)
        return self
