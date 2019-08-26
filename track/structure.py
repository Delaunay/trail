""" hold basic data type classes that all backends need to implement """

from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from track.versioning import compute_hash


class Status(Enum):
    CreatedGroup = 0    # was created nothing is planed for it at the moment

    RunningGroup = 100  # is running
    Running = 101

    ErrorGroup = 200   # Not Running; because:
    Interrupted = 201  # -> SIGTERM
    Exception = 202    # -> Exception was raised
    Broken = 203       # -> multiple error occured, will not be retried

    FinishedGroup = 300  # Not Running because:
    Suspended = 301      # -> was suspended by the user
    Completed = 302      # -> has finished running


_STATUS_INT = set(map(lambda x: x.value, Status.__members__.values()))
_STATUS_STR = set(map(lambda x: x.name, Status.__members__.values()))


class CustomStatus:
    def __init__(self, name, value):
        self._name = name
        self._value = value

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return f'CStatus<{self.name}>'

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.value == other.get('value') and self.name == other.get('name')

        if isinstance(other, str):
            return self.name == other

        return self.value == other.value and self.name == other.name


def status(name=None, value=None):
    if name is not None:
        if name in _STATUS_STR:
            return Status.__members__[name]

        return CustomStatus(name, value)

    if value is not None:
        if value in _STATUS_INT:
            return Status(value)

        return CustomStatus(name, value)


@dataclass
class Trial:
    """ A single training run """
    @property
    def uid(self) -> str:
        return f'{self.hash}_{self.revision}'

    @uid.setter
    def uid(self, value):
        h, r = value.rsplit('_', maxsplit=1)
        self._hash = h
        self.revision = r

    @property
    def hash(self):
        if self._hash is None:
            self._hash = self.compute_hash()
        return self._hash

    @hash.setter
    def hash(self, v):
        self._hash = v

    def compute_hash(self) -> str:
        return compute_hash(self.name, self.version, **self.parameters)

    _hash: str = None
    revision: int = 0                   # if uid is a duplicate rev += 1
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Dict[str, any] = field(default_factory=dict)

    version: Optional[str] = None
    group_id: Optional[int] = None
    project_id: Optional[int] = None

    # Arguments and parameters
    parameters: Dict[str, any] = field(default_factory=dict)
    # Meta data about the trial
    metadata: Dict[str, any] = field(default_factory=dict)
    # Training metrics
    metrics: Dict[str, any] = field(default_factory=dict)
    # Timers are saved here
    chronos: Dict[str, any] = field(default_factory=dict)
    status: Optional[Status] = Status.CreatedGroup

    # List of errors that occurred during the training
    errors: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other):
        return hash(other) == hash(self.uid)


@dataclass
class TrialGroup:
    """ Namespace / Set of trials """

    def compute_uid(self) -> str:
        assert self.project_id is not None, f'Trial Group (name: {self.name}) needs to be associated with a project'
        assert self.name is not None, f'Trial Group for (project: {self.project_id}) has no name!'

        return compute_hash(self.name, self.project_id)

    @property
    def uid(self):
        if self._uid is None:
            self._uid = self.compute_uid()
        return self._uid

    _uid: str = None
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)
    trials: Set[Trial] = field(default_factory=set)

    project_id: Optional[int] = None

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other):
        return hash(other) == hash(self.uid)


@dataclass
class Project:
    """ Set of Trial Groups & trials
        If projects define tags than all children inherit those tags.
        children cannot override the tag of a parent
    """
    def compute_uid(self) -> str:
        assert self.name is not None, f'Project need a name!'
        return self.name

    @property
    def uid(self):
        if self._uid is None:
            self._uid = self.compute_uid()
        return self._uid

    _uid: str = None
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)
    groups: Set[TrialGroup] = field(default_factory=set)
    trials: Set[Trial] = field(default_factory=set)

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other):
        return hash(other) == hash(self.uid)


_current_project = None
_current_trial = None


def get_current_project():
    return _current_project


def get_current_trial():
    return _current_trial


def set_current_project(project):
    global _current_project
    _current_project = project
    return _current_project


def set_current_trial(trial):
    global _current_trial
    _current_trial = trial
    return _current_trial


if __name__ == '__main__':

    print(status(name='Running'))
    print(status(value=101))
    print(status(name='test', value=23))

