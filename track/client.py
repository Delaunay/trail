import json
import os

from typing import Union, Callable, Dict, Optional

from argparse import ArgumentParser, Namespace
from track.structure import Trial, Project, TrialGroup

from track.logger import TrialLogger
from track.persistence import get_protocol
from track.serialization import to_json
from track.versioning import default_version_hash
from track.configuration import options
from track.utils.delay import delay_call, is_delayed_call
from track.utils.log import warning, debug, info


class TrialDoesNotExist(Exception):
    pass


# pylint: disable=too-many-public-methods
class TrackClient:
    """ TrackClient. A client tracks a single Trial being ran

    Parameters
    ----------
    backend: str
        Storage backend to use
    """

    def __init__(self, backend=options('log.backend.name', default='none')):
        self.project = None
        self.group = None
        self.trial = None

        self.protocol = get_protocol(backend)
        self.logger: TrialLogger = None
        self.set_version()

        self.version = None
        self.set_version()

        # Orion integration
        # -----------------
        orion_name = os.environ.get('ORION_PROJECT')
        if orion_name is not None:
            self.set_project(name=orion_name, get_only=True)

        orion_exp = os.environ.get('ORION_EXPERIMENT')
        if orion_exp is not None:
            self.set_group(name=orion_exp, get_only=True)

        orion_trial = os.environ.get('ORION_TRIAL_ID')
        if orion_trial is not None:
            self.set_trial(uid=orion_trial)

    def set_version(self, version=None, version_fun: Callable[[], str] = None):
        """Compute the version tag from the function call stack. Defaults to compute the hash of the executed file

        Parameters
        ----------
        version: str
            version string you want to use for the trial

        version_fun: Callable[[], str]
            version function to call to set the trial version
        """
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

    def set_project(self, project: Optional[Project] = None, force: bool = False, get_only: bool = False, **kwargs):
        """Set or create a new project

        Parameters
        ----------
        project: Optional[Project]
            project definition you can use to create or set the project

        force: bool
            by default once the project is set it cannot be changed.
            use force to override this behaviour.

        get_only: bool
            if true does not insert the project if missing.
            default to false

        kwargs
            arguments used to create a `Project` object if no project object were provided
            See :func:`~track.structure.Project` for possible arguments

        Returns
        -------
        returns created project
        """
        if self.project is not None and not force:
            info('Project is already set, to override use force=True')
            return self.project

        if project is None:
            project = Project(**kwargs)

        assert project.name is not None, 'Project name cannot be none'

        # does the project exist ?
        self.project = self.protocol.get_project(project)

        if self.project is not None:
            return self.project

        if get_only:
            raise RuntimeError(f'Project (name: {project.name}) was not found!')

        self.project = self.protocol.new_project(project)

        debug(f'set project to (project: {self.project.name})')
        return self.project

    def set_group(self, group: Optional[TrialGroup] = None, force: bool = False, get_only: bool = False, **kwargs):
        """Set or create a new group

        Parameters
        ----------
        group: Optional[TrialGroup]
            project definition you can use to create or set the project

        force: bool
            by default once the trial group is set it cannot be changed.
            use force to override this behaviour.

        get_only: bool
            if true does not insert the group if missing.
            default to false

        kwargs
            arguments used to create a `TrialGroup` object if no TrialGroup object were provided.
            See :func:`~track.structure.TrialGroup` for possible arguments

        Returns
        -------
        returns created trial group
        """

        if self.group is not None and not force:
            info('Group is already set, to override use force=True')
            return self.group

        if group is None:
            group = TrialGroup(**kwargs)

        if group.project_id is None:
            group.project_id = self.project.uid

        self.group = self.protocol.get_trial_group(group)

        if self.group is not None:
            return self.group

        if get_only:
            raise RuntimeError(f'Group (name: {group.name}) was not found!')

        self.group = self.protocol.new_trial_group(group)
        return self.group

    def set_trial(self, trial: Optional[Trial] = None, force: bool = False, **kwargs):
        """Set a new trial

        Parameters
        ----------
        trial: Optional[Trial]
            project definition you can use to create or set the project

        force: bool
            by default once the trial is set it cannot be changed.
            use force to override this behaviour.

        kwargs: {uid, hash, revision}
            arguments used to create a `Trial` object if no Trial object were provided.
            You should specify `uid` or the pair `(hash, revision)`.
            See :func:`~track.structure.Trial` for possible arguments

        Returns
        -------
        returns a trial logger
        """
        if self.trial is not None and not force:
            info('Trial is already set, to override use force=True')
            return self.logger

        if trial is None:
            uhash = kwargs.pop('hash', None)
            uid = kwargs.pop('uid', None)
            version = kwargs.pop('version', self.version())

            trial = Trial(version=version, **kwargs)
            if uhash is not None:
                trial.hash = uhash

            if uid is not None:
                trial.uid = uid

        try:
            if trial.version is None:
                trial.version = self.version()

            trials = self.protocol.get_trial(trial)

            if trials is None:
                raise TrialDoesNotExist(
                    f'Trial (hash: {trial.hash}, v:{trial.version} rev: {trial.revision}) does not exist!')

            self.trial = trials[0]
            self.logger = TrialLogger(self.trial, self.protocol)
            return self.logger

        except IndexError:
            raise TrialDoesNotExist(f'cannot set trial (id: {trial.uid}, hash:{hash}) it does not exist')

    def _new_trial(self, force=False, parameters=None, **kwargs):
        """Create a new trial if all the required arguments are satisfied.

        To provide a better user experience if not all arguments are provided a delayed trials is created
        that holds all the data provided and will create the trial once all arguments are ready.
        Currently only `arguments` i.e the parameters of the experience is required. This is
        because they are needed to compute the trial uid (which is a hash of the parameters).

        If no project is set, the trial is inserted in a catch all project named `orphan`

        Parameters
        ----------
        force: bool
            by default once the trial is set it cannot be changed.
            use force to override this behaviour.

        kwargs
            See :func:`~track.structure.Trial` for possible arguments

        Returns
        -------
        returns a trial
        """
        if isinstance(parameters, Namespace):
            parameters = dict(**vars(parameters))

        if self.trial is not None and not is_delayed_call(self.trial) and not force:
            info(f'Trial is already set, to override use force=True')
            return self.trial

        # if arguments are not specified do not create the trial just yet
        # wait for the user to be able to specify the parameters so we can have a meaningful hash
        if parameters is None:
            if is_delayed_call(self.trial):
                raise RuntimeError('Trial needs parameters')

            self.trial = delay_call(self._new_trial, **kwargs)
            # return the logger with the delayed trial
            return self.trial

        # replace the trial or delayed trial by its actual value
        if parameters or is_delayed_call(self.trial):
            self.trial = self._make_trial(parameters=parameters, **kwargs)

        if self.project is None:
            self.project = self.set_project(name='orphan')

        self.protocol.add_project_trial(self.project, self.trial)

        if self.group is not None:
            self.protocol.add_group_trial(self.group, self.trial)

        return self.trial

    def new_trial(self, force=False, **kwargs):
        """Create a new trial

        Parameters
        ----------
        force: bool
            by default once the trial is set it cannot be changed.
            use force to override this behaviour.

        kwargs:
            See :func:`~track.structure.Trial` for possible arguments

        Returns
        -------
        returns a trial logger
        """
        self.trial = self._new_trial(force, **kwargs)
        self.logger = TrialLogger(self.trial, self.protocol)
        return self.logger

    def _make_trial(self, parameters, name=None, **kwargs):
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
            parameters=parameters,
            **kwargs)

        trial = self.protocol.new_trial(trial)
        print(trial)
        assert trial is not None
        return trial

    def add_tags(self, **kwargs):
        """Insert tags to current trials"""
        # We do not need to create the trial to add tags.
        # just append the tags to the trial call when it is going to be created
        if is_delayed_call(self.trial):
            self.trial.add_arguments(tags=kwargs)
        else:
            self.logger.add_tags(**kwargs)

    def get_arguments(self, args: Union[ArgumentParser, Namespace, Dict] = None, show=False, **kwargs) -> Namespace:
        """See :func:`~track.client.log_arguments` for possible arguments"""
        return self.log_arguments(args, show, **kwargs)

    def log_arguments(self, args: Union[ArgumentParser, Namespace, Dict] = None, show=False, **kwargs) -> Namespace:
        """Store the arguments that was used to run the trial.

        Parameters
        ----------
        args: Union[ArgumentParser, Namespace, Dict]
            save up the trial's arguments

        show: bool
            print the arguments on the command line

        kwargs
            more trial's arguments

        Returns
        -------
        returns the trial's arguments
        """
        nargs = dict()
        if args is not None:
            nargs = args

        if isinstance(args, ArgumentParser):
            nargs = args.parse_args()

        if isinstance(nargs, Namespace):
            nargs = dict(**vars(nargs))

        kwargs.update(nargs)

        # if we have a pending trial create it now as we have all the information
        if is_delayed_call(self.trial):
            self.trial = self.trial(parameters=kwargs)
            self.logger = TrialLogger(self.trial, self.protocol)
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
        """Try to use the backend attributes if not available"""

        if is_delayed_call(self.trial):
            warning('Creating a trial without parameters!')
            self.logger = self.trial()
            self.trial = self.logger.trial

        # Look for the attribute in the top level logger
        if hasattr(self.logger, item):
            return getattr(self.logger, item)

        raise AttributeError(item)

    def report(self, short=True):
        """Print a digest of the logged metrics"""
        self.logger.finish()
        print(json.dumps(to_json(self.trial, short), indent=2))
        return self

    def save(self, file_name_override=None):
        """Saved logged metrics into a json file"""
        self.protocol.commit(file_name_override=file_name_override)

    @staticmethod
    def get_device():
        """Helper function that returns a cuda device if available else a cpu"""
        import torch

        if torch.cuda.is_available():
            return torch.device('cuda')
        return torch.device('cpu')

    def finish(self, exc_type=None, exc_val=None, exc_tb=None):
        return self.logger.finish(exc_type, exc_val, exc_tb)

    def start(self):
        return self.logger.start()

    def __enter__(self):
        return self.logger.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.logger.__exit__(exc_type, exc_val, exc_tb)
