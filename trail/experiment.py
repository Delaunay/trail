import json
import inspect
from dataclasses import dataclass, field
from typing import List, Union, Callable

from argparse import ArgumentParser, Namespace

from benchutils.statstream import StatStream
from trail.utils.throttle import throttled
from trail.containers.types import float32
from trail.trial import Trial

from trail.aggregators.aggregator import Aggregator
from trail.aggregators.aggregator import RingAggregator
from trail.aggregators.aggregator import StatAggregator
from trail.aggregators.aggregator import TimeSeriesAggregator

from trail.logger import Logger
from trail.persistence import build_logger
from trail.utils.system import get_gpu_name
from trail.serialization import to_json
from trail.versioning import get_file_version
from trail.utils.eta import EstimatedTime
from trail.configuration import options
from trail.utils.out import RingOutputDecorator


ring_aggregator = RingAggregator.lazy(10, float32)
stat_aggregator = StatAggregator.lazy(1)
ts_aggregator = TimeSeriesAggregator.lazy()
current_trial = None
current_logger = None
current_experiment = None


def get_current_trial():
    return current_trial


def get_current_logger():
    return current_logger


def get_current_experiment():
    return current_experiment


@dataclass
class ExperimentData:
    name: str = None
    description: str = None
    models: List[any] = None
    data_set: any = None
    optimizers: any = None
    hyper_parameters: List[str] = None
    parameters: List[str] = None
    trials: List[Trial] = field(default_factory=list)


class Experiment:
    """ An experiment is a set of trials. Trials are """

    def __init__(self, experiment_name, trial_name: str = None, description: str = None,
                 backend=options('log.backend.name', default='none'), **kwargs):
        global current_trial
        global current_logger
        global current_experiment

        self.exp = ExperimentData(experiment_name, description)
        current_experiment = self.exp

        self.current_trial = Trial(name=trial_name)
        current_trial = self.current_trial
        self.exp.trials.append(self.current_trial)

        self.logger: Logger = Logger(self.current_trial, build_logger(backend, **kwargs))
        current_logger = self.logger
        self.eta = EstimatedTime(None, 1)

        self.top_level_file = None
        self._system_info()
        self._version_info()

        self.stderr = None
        self.stdout = None
        self.batch_printer = None
        
    def __getattr__(self, item):
        """ try to use the backend attributes if not available """
        if hasattr(self.logger.backend.exp, item):
            return getattr(self.logger.backend.exp, item)

        raise AttributeError(item)

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

    def get_arguments(self, args: Union[ArgumentParser, Namespace], show=False) -> Namespace:
        """ Store the arguments that was used to run the trial.
        """

        if isinstance(args, ArgumentParser):
            args = args.parse_args()

        args = self.apply_overrides(args)
        self.logger.log_arguments(args)

        if show:
            print('-' * 80)
            for k, v in vars(args).items():
                print(f'{k:>30}: {v}')
            print('-' * 80)

        return args

    def apply_overrides(self, args: Namespace) -> Namespace:
        return args

    def show_eta(self, step: int, timer: StatStream, msg: str = '', throttle=None, every=None, no_print=False):
        self.eta.timer = timer

        if self.batch_printer is None:
            self.batch_printer = throttled(self.eta.show_eta, throttle, every)

        if not no_print:
            self.batch_printer(step, msg)

    def report(self, short=True):
        """ print a digest of the logged metrics """
        self.logger.finish()
        print(json.dumps(to_json(self.current_trial, short), indent=2))

    def save(self, file_name):
        """ saved logged metrics into a json file """
        with open(file_name, 'w') as out:
            json.dump(to_json(self.current_trial), out, indent=2)

    def log_metrics(self, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        return self.logger.log_metrics(step=step, aggregator=aggregator, **kwargs)

    def chrono(self, name: str, aggregator: Callable[[], Aggregator] = stat_aggregator, sync=None):
        """ create a chrono context to time the runtime of the code inside it"""
        return self.logger.chrono(name, aggregator, sync)

    @staticmethod
    def get_device():
        """ helper function that returns a cuda device if available else a cpu"""
        import torch

        if torch.cuda.is_available():
            return torch.device('cuda')
        return torch.device('cpu')

    # -- Getter Setter
    def set_eta_total(self, t):
        self.eta.set_totals(t)

    def capture_output(self):
        import sys
        sys.stdout = RingOutputDecorator(file=sys.stdout, n_entries=50)
        sys.stderr = RingOutputDecorator(file=sys.stderr, n_entries=50)

    # Context API for starting the top level chrono
    def finish(self, exc_type=None, exc_val=None, exc_tb=None):
        self.logger.finish(exc_type, exc_val, exc_tb)

    def start(self):
        self.logger.start()

    def __enter__(self):
        self.logger.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.finish(exc_type, exc_val, exc_tb)

