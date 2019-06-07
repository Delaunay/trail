import json
import os
import inspect
from typing import Union

from argparse import ArgumentParser, Namespace

from benchutils.statstream import StatStream
from track.utils.throttle import throttled
from track.struct import Trial, Project, TrialGroup, set_current_project, set_current_trial


from track.logger import Logger
from track.persistence import build_logger
from track.serialization import to_json
from track.versioning import get_file_version
from track.utils.eta import EstimatedTime
from track.configuration import options
from track.utils.out import RingOutputDecorator

from track.utils.log import warning


class TrailClient:
    """ An experiment is a set of trials. Trials are """

    def __init__(self, backend=options('log.backend.name', default='none'), **kwargs):
        self.project = None
        self.group = None
        self.trial = Trial()

        set_current_trial(self.trial)

        self.logger: Logger = Logger(self.trial, build_logger(backend, **kwargs))
        self.eta = EstimatedTime(None, 1)

        self.top_level_file = None
        # self._system_info()
        # self._version_info()

        self.stderr = None
        self.stdout = None
        self.batch_printer = None

    def new_trial(self, name=None, description=None):
        self.trial = Trial(name=name, description=description)

    def set_project(self, project=None, name=None, tags=None, description=None):
        if project is None:
            project = Project(name=name, tags=tags, description=description)
            self.project = project

        if self.group is not None:
            project.groups.append(self.group.uid)
            self.group.project_id = self.project.uid

        set_current_project(project)
        project.trials.append(self.trial)
        self.logger.set_project(project)
        return self

    def set_group(self, group=None, name=None, tags=None, description=None):
        if self.project is None:
            raise RuntimeError('Project needs to be set to define a group')

        if group is None:
            group = TrialGroup(name=name, tags=tags, description=description)
            self.group = group

        if self.project is not None:
            group.project_id = self.project.uid
            self.project.groups.append(self.group.uid)

        group.trials.append(self.trial.uid)
        self.logger.set_group(group)
        return self

    def get_arguments(self, args: Union[ArgumentParser, Namespace], show=False) -> Namespace:
        """ Store the arguments that was used to run the trial.  """

        if isinstance(args, ArgumentParser):
            args = args.parse_args()

        self.logger.log_arguments(args)

        if show:
            print('-' * 80)
            for k, v in vars(args).items():
                print(f'{k:>30}: {v}')
            print('-' * 80)

        return args

    def __getattr__(self, item):
        """ try to use the backend attributes if not available """
        #def chainer(fun):
        #    def _chainer(*args, **kwargs):
        #        fun(*args, **kwargs)
        #        return self
        #    return _chainer

        # Look for the attribute in the top level logger
        if hasattr(self.logger, item):
            return getattr(self.logger, item)

        # Look for the attribute in the backend
        if hasattr(self.logger.backend, item):
            return getattr(self.logger.backend, item)

        raise AttributeError(item)

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

    def show_eta(self, step: int, timer: StatStream, msg: str = '',
                 throttle=options('log.print.throttle', None),
                 every=options('log.print.every', None),
                 no_print=options('log.print.disable', False)):

        self.eta.timer = timer

        if self.batch_printer is None:
            self.batch_printer = throttled(self.eta.show_eta, throttle, every)

        if not no_print:
            self.batch_printer(step, msg)

    def report(self, short=True):
        """ print a digest of the logged metrics """
        self.logger.finish()
        print(json.dumps(to_json(self.trial, short), indent=2))

    def save(self, file_name=options('log.save', default=None)):
        """ saved logged metrics into a json file """

        if file_name is None:
            warning('No output file specified')
            return

        initial_data = []
        if os.path.exists(file_name):
            initial_data = json.load(open(file_name, 'r'))

        if self.project is not None:
            initial_data.append(to_json(self.project))
        else:
            initial_data.append(to_json(self.trial))

        with open(file_name, 'w') as out:
            json.dump(initial_data, out, indent=2)

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
        do_stderr = sys.stderr is not sys.stdout
        sys.stdout = RingOutputDecorator(file=sys.stdout, n_entries=options('log.stdout_capture', 50))

        if do_stderr:
            sys.stderr = RingOutputDecorator(file=sys.stderr, n_entries=options('log.stderr_capture', 50))

    def finish(self, exc_type=None, exc_val=None, exc_tb=None):
        return self.logger.finish(exc_type, exc_val, exc_tb)

    def start(self):
        return self.logger.start()

    def __enter__(self):
        return self.logger.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.logger.__exit__(exc_type, exc_val, exc_tb)

