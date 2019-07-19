import json
import inspect
import os
from typing import Union, Callable, Dict

from argparse import ArgumentParser, Namespace

from benchutils.statstream import StatStream
from track.utils.throttle import throttled
from track.structure import Trial, Project, TrialGroup

from track.logger import TrialLogger
from track.persistence import get_protocol
from track.serialization import to_json
from track.versioning import default_version_hash
from track.utils.eta import EstimatedTime
from track.configuration import options
from track.utils.out import RingOutputDecorator
from track.utils.delay import delay_call, is_delayed_call
from track.utils.log import warning, debug


# pylint: disable=too-many-public-methods
class TrackClient:
    """ TrackClient. A client tracks a single Trial being ran"""

    def __init__(self, backend=options('log.backend.name', default='none')):

        self.project = None
        self.group = None
        self.trial = None

        self.protocol = get_protocol(backend)
        self.logger: TrialLogger = None
        self.eta = EstimatedTime(None, 1)

        self.code = None
        self.stderr = None
        self.stdout = None
        self.batch_printer = None
        self.set_version()

        self.version = None
        self.set_version()

        # Orion integration
        # -----------------
        orion_name = os.environ.get('ORION_PROJECT')
        if orion_name is not None:
            self.set_project(name=orion_name)

        orion_exp = os.environ.get('ORION_EXPERIMENT')
        if orion_exp is not None:
            self.set_group(name=orion_exp)

        orion_trial = os.environ.get('ORION_TRIAL_ID')
        if orion_trial is not None:
            self.set_trial(uid=orion_trial)

    def set_version(self, version=None, version_fun: Callable[[], str] = None):
        """Compute the version tag from the function call stack. Defaults to compute the hash of the executed file"""
        def version_compute():
            fun = version_fun
            if fun is None:
                fun = default_version_hash

            if version is None:
                return fun()
            else:
                return version

        self.version = version_compute
        return self

    def set_project(self, project=None, name=None, tags=None, description=None, force=False):
        if self.project is not None and not force:
            warning('Project is already set, to override use force=True')
            return self.project

        if project is None:
            project = Project(name=name, tags=tags, description=description)

        assert project.name is not None, 'Project name cannot be none'

        # does the project exist ?
        self.project = self.protocol.get_project(project)

        if self.project is not None:
            return self.project

        self.project = self.protocol.new_project(project)

        debug(f'set project to (project: {self.project.name})')
        return self.project

    def set_group(self, group: TrialGroup = None, name=None, tags=None, description=None, force=False):
        if self.group is not None and not force:
            warning('Group is already set, to override use force=True')
            return self.group

        if group is None:
            group = TrialGroup(name=name, tags=tags, description=description, project_id=self.project.uid)

        if group.project_id is None:
            group.project_id = self.project.uid

        self.group = self.protocol.get_trial_group(group)

        if self.group is not None:
            return self.group

        self.group = self.protocol.new_trial_group(group)
        return self.group

    def _make_trial(self, arguments, name=None, **kwargs):
        project_id = None
        group_id = None
        if self.project is not None:
            project_id = self.project.uid

        if self.group is not None:
            group_id = self.group.uid

        trial = Trial(
            name=name,
            version=self.version(),
            project_id=project_id,
            group_id=group_id,
            parameters=arguments,
            **kwargs)

        trial = self.protocol.new_trial(trial)
        return trial

    def set_trial(self, uid=None, hash=None, revision=None, force=False):
        if self.trial is not None and not force:
            warning('Trial is already set, to override use force=True')
            return self.logger

        if uid is not None:
            hash, revision = uid.split('_')
        else:
            assert hash is not None and revision is not None

        try:
            self.trial = self.protocol.get_trial(Trial(_hash=hash, revision=revision))[0]
            self.logger = TrialLogger(self.trial, self.protocol)
            return self.logger

        except IndexError:
            raise RuntimeError(f'cannot set trial (id: {uid}, hash:{hash}) it does not exist')

    def new_trial(self, arguments=None, name=None, description=None, force=False, **kwargs):
        if self.trial is not None and not force:
            warning('Trial is already set, to override use force=True')
            return self.logger

        # if arguments are not specified do not create the trial just yet
        # wait for the user to be able to specify the parameters so we can have a meaningful hash
        if arguments is None:
            if is_delayed_call(self.trial):
                raise RuntimeError('Trial needs arguments')

            self.trial = delay_call(self.new_trial, name=name, description=description, **kwargs)
            return self.trial.get_future()

        # replace the trial or delayed trial by its actual value
        if self.trial is None or is_delayed_call(self.trial):
            self.trial = self._make_trial(arguments, name=name)

        self.logger = TrialLogger(self.trial, self.protocol)

        if self.project is not None:
            self.protocol.add_project_trial(self.project, self.trial)

        if self.group is not None:
            self.protocol.add_group_trial(self.group, self.trial)

        return self.logger

    def add_tags(self, **kwargs):
        # We do not need to create the trial to add tags.
        # just append the tags to the trial call when it is going to be created
        if is_delayed_call(self.trial):
            self.trial.add_arguments(**kwargs)
        else:
            self.logger.add_tags(**kwargs)

    def get_arguments(self, args: Union[ArgumentParser, Namespace, Dict], show=False, **kwargs) -> Namespace:
        return self.log_arguments(args, show, **kwargs)

    def log_arguments(self, args: Union[ArgumentParser, Namespace, Dict], show=False, **kwargs) -> Namespace:
        """ Store the arguments that was used to run the trial.  """

        nargs = args
        if isinstance(args, ArgumentParser):
            nargs = args.parse_args()

        if isinstance(nargs, Namespace):
            nargs = dict(**vars(nargs))

        kwargs.update(nargs)

        # if we have a pending trial create it now as we have all the information
        if is_delayed_call(self.trial):
            self.trial(arguments=kwargs)
        else:
            # we do not need to log the arguments they are inside the trial already
            self.logger.log_arguments(**kwargs)

        if show:
            print('-' * 80)
            for k, v in vars(args).items():
                print(f'{k:>30}: {v}')
            print('-' * 80)

        return args

    def __getattr__(self, item):
        """ try to use the backend attributes if not available """

        if is_delayed_call(self.trial):
            warning('Creating a trial without parameters!')
            self.trial()

        # Look for the attribute in the top level logger
        if hasattr(self.logger, item):
            return getattr(self.logger, item)

        raise AttributeError(item)

    def log_code(self):
        self.code = open(inspect.stack()[-1].filename, 'r').read()
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

    def report(self, short=True):
        """ print a digest of the logged metrics """
        self.logger.finish()
        print(json.dumps(to_json(self.trial, short), indent=2))
        return self

    def save(self, file_name_override=None):
        """ saved logged metrics into a json file """
        self.protocol.commit(file_name_override=file_name_override)

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
        return self

    def capture_output(self):
        import sys
        do_stderr = sys.stderr is not sys.stdout

        self.stdout = RingOutputDecorator(file=sys.stdout, n_entries=options('log.stdout_capture', 50))
        sys.stdout = self.stdout

        if do_stderr:
            self.stderr = RingOutputDecorator(file=sys.stderr, n_entries=options('log.stderr_capture', 50))
            sys.stderr = self.stderr
        return self

    def finish(self, exc_type=None, exc_val=None, exc_tb=None):
        return self.logger.finish(exc_type, exc_val, exc_tb)

    def start(self):
        return self.logger.start()

    def __enter__(self):
        return self.logger.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.logger.__exit__(exc_type, exc_val, exc_tb)
