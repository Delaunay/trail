import json
import inspect
from dataclasses import dataclass, field
from typing import List, Union, Callable
import torch
from torch.nn import Module
import torch.cuda

from argparse import ArgumentParser, Namespace

from benchutils.statstream import StatStream
from trail.utils.throttle import throttled
from trail.containers.types import float32
from trail.trial import Trial

from trail.chrono import ChronoContext
from trail.aggregators.aggregator import Aggregator
from trail.aggregators.aggregator import RingAggregator
from trail.aggregators.aggregator import StatAggregator
from trail.aggregators.aggregator import ValueAggregator
from trail.aggregators.aggregator import TimeSeriesAggregator

from trail.utils.system import get_gpu_name
from trail.serialization import to_json
from trail.versioning import get_file_version, get_git_version


ring_aggregator = RingAggregator.lazy(10, float32)
stat_aggregator = StatAggregator.lazy(1)
ts_aggregator = TimeSeriesAggregator.lazy()
current_trial = None
current_logger = None


def get_current_trial():
    return current_trial


def get_current_logger():
    return current_logger


@dataclass
class ExperimentData:
    name: str = None
    description: str = None
    models: List[Module] = None
    data_set: any = None
    optimizers: any = None
    hyper_parameters: List[str] = None
    parameters: List[str] = None
    trials: List[Trial] = field(default_factory=list)


class Experiment:
    """ An experiment is a set of trials. Trials are """

    def __init__(self, experiment_name, trial_name: str = None, description: str = None):
        global current_trial
        global current_logger

        self.exp = ExperimentData(experiment_name, description)
        self.current_trial = Trial(name=trial_name)
        current_trial = self.current_trial
        self.exp.trials.append(self.current_trial)

        self.epoch_printer = None
        self.epoch_id = 0
        self.epoch_total = 0

        self.batch_printer = None
        self.batch_id = 0
        self.batch_total = 0

        self.depth = 0
        acc = ValueAggregator()
        self.parent_chrono = ChronoContext('runtime', acc, None, self)
        self.current_trial.values['runtime'] = acc
        # self.attr_metrics = {}

        self.top_level_file = None
        self._system_info()
        self._version_info()
        self.start()

    def _system_info(self):
        self.current_trial.system_metrics['gpu'] = {
            'name': get_gpu_name()
        }

    def _version_info(self):
        """ inspect the call stack to find where the main is located and use the main to compute the version"""
        # File hash             # Only works if the main.py was the only file that was modified
        # Git Hash              # Only if inside a git repository
        # Git Diff hash         # Only if inside a git repository
        # Hyper Parameter Hash  # For Trials where only hyper params change
        # Param Hash            # For experiment

        call_stack = inspect.stack()
        first_call = call_stack[-1]
        self.top_level_file = first_call.filename
        self.current_trial.version = get_file_version(self.top_level_file)

    def _log_code(self):
        self.current_trial = open(self.top_level_file, 'r').read()

    def __getattr__(self, name):
        if not name.startswith('log_'):
            raise AttributeError(name)

        metric_name = name[4:]

        #if metric_name not in self.current_trial.metrics:
        #    return self._attr_metric_constructor

        return self._partial_log_metric(metric_name)

    def _partial_log_metric(self, name):
        def partial(*args, **kwargs):
            return self._log_value(name, *args, **kwargs)
        return partial

    def _attr_metric_constructor(self, *args, **kwargs):
        """ we can preprocess the args if necessary here """

        return self.log_metric(*args, **kwargs)

    def get_arguments(self, args: Union[ArgumentParser, Namespace], show=False) -> Namespace:
        """ Store the arguments that was used to run the trial.
            If an hyper parameter optimizer is used some overrides might be applied to the parameters
        """

        if isinstance(args, ArgumentParser):
            args = args.parse_args()

        args = self.apply_overrides(args)
        self.current_trial.args = args

        if show:
            print('-' * 80)
            for k, v in vars(args).items():
                print(f'{k:>30}: {v}')
            print('-' * 80)

        return args

    def apply_overrides(self, args: Namespace) -> Namespace:
        return args

    def show_epoch_eta(self, epoch_id: int, total: int, timer: StatStream, msg: str = '',
                       throttle=None, every=None, no_print=False):

        if self.epoch_printer is None:
            self.epoch_printer = throttled(epoch_eta_print, throttle, every)

        # maybe we do not know the numbers of epochs
        self.epoch_total = max(epoch_id, total, self.epoch_total)
        self.epoch_id = epoch_id

        if not no_print:
            self.epoch_printer(epoch_id, self.epoch_total, timer, msg)

    def show_batch_eta(self, batch_id: int, total: int, timer: StatStream, msg: str = '',
                       throttle=None, every=None, no_print=False):

        if self.batch_printer is None:
            self.batch_printer = throttled(batch_eta_print, throttle, every)

        # maybe we do not know the numbers of batch per epoch
        self.batch_total = max(batch_id, total, self.batch_total)
        self.batch_id = batch_id

        if not no_print:
            self.batch_printer(self.epoch_id, self.epoch_total, batch_id, self.batch_total, timer, msg)

    def finish(self):
        self.parent_chrono.__exit__(None, None, None)

    def start(self):
        self.parent_chrono.__enter__()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.parent_chrono.__exit__(exc_type, exc_val, exc_tb)

    def report(self, short=True):
        self.finish()
        print(json.dumps(to_json(self.current_trial, short), indent=2))

    def log_batch_loss(self, val: any, step=None):
        return self.log_metric('batch_loss', val, step, ts_aggregator)

    # Log a metric that is not linked to a particular step in the training process
    def _log_value(self, key, value, aggregator: Callable[[], Aggregator] = ring_aggregator):
        storage = self.current_trial.values
        agg = storage.get(key)

        if agg is None:
            agg = aggregator()
            storage[key] = agg

        agg.append(value)

    # log a dictionary of metrics for a given step
    def _log_metric(self, step, **kwargs):
        self.current_trial.metrics[step].update(kwargs)

    def log_metrics(self, step: any = None, aggregator: Callable[[], Aggregator] = ring_aggregator, **kwargs):
        if step is None:
            for k, v in kwargs.items():
                self._log_value(k, v, aggregator)
        else:
            self._log_metric(step, **kwargs)

    def chrono(self, name: str, aggregator: Callable[[], Aggregator] = stat_aggregator, sync=None):
        """ create a chrono context to time the runtime of the code inside it"""
        agg = self.current_trial.values.get(name)
        if agg is None:
            agg = aggregator()
            self.current_trial.values[name] = agg

        return ChronoContext(name, agg, sync, self.parent_chrono)

    @staticmethod
    def get_device():
        """ helper function that returns a cuda device if available else a cpu"""
        if torch.cuda.is_available():
            return torch.device('cuda')
        return torch.device('cpu')

    # -- Getter Setter
    def set_total_epoch(self, t):
        self.epoch_total = t

    def set_epoch(self, t):
        self.epoch_id = t

    def set_batch_count(self, b):
        self.batch_total = b

    def set_batch_id(self, b):
        self.batch_id = b


def default_epoch_eta_print(epoch_id: int, epoch_total: int, timer: StatStream, msg: str):
    if msg:
        msg = ' | ' + msg

    eta = _get_time(timer) * (epoch_total - (epoch_id + 1)) / 60
    eta = f' | Train ETA: {eta:6.2f} min'

    print(f'[{epoch_id + 1:3d}/{epoch_total:3d}][    /    ]{eta} {msg}')


def default_batch_eta_print(epoch_id: int, epoch_total: int,
                            batch_id: int, batch_total: int, timer: StatStream, msg: str):
    if msg:
        msg = ' | ' + msg

    eta = _get_time(timer) * (batch_total - (batch_id + 1)) / 60
    if epoch_total == 0:
        eta = ''
    else:
        eta = f' | - Epoch ETA: {eta:6.2f} min'

    print(f'[{epoch_id + 1:3d}/{epoch_total:3d}][{batch_id:4d}/{batch_total:4d}]{eta} {msg}')


epoch_eta_print = default_epoch_eta_print
batch_eta_print = default_batch_eta_print


def _get_time(time: StatStream):
    avg = time.avg
    if avg == 0:
        return time.val
    return avg

