""" hold basic data type classes that all backends need to implement """

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class Status(Enum):
    RunningGroup = 100  # is running
    Running = 101

    ErrorGroup = 200   # Not Running; because:
    Interrupted = 201  # -> SIGTERM
    Exception = 202    # -> Exception was raised
    Broken = 203       # -> multiple error occured, will not be retried

    FinishedGroup = 300  # Not Running because:
    Suspended = 301      # -> was suspended by the user
    Completed = 302      # -> has finished running


@dataclass
class Trial:
    """ A single training run """
    @property
    def uid(self):
        return f'{self.trial_hash}_{self.revision}'

    trial_hash: str = None              # name x version x parameters
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
    status: Optional[Status] = None
    # List of errors that occurred during the training
    errors: List[str] = field(default_factory=list)

    def __hash__(self):
        return self.uid


@dataclass
class TrialGroup:
    """ Namespace / Set of trials """

    uid: Optional[str] = None           # name x project_id
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    trials: List[Trial] = field(default_factory=list)

    project_id: Optional[int] = None


@dataclass
class Project:
    """ Set of Trial Groups & trials
        If projects define tags than all children inherit those tags.
        children cannot override the tag of a parent
    """

    uid: Optional[str] = None           # name
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    groups: List[TrialGroup] = field(default_factory=list)
    trials: List[Trial] = field(default_factory=list)


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


