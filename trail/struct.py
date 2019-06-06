""" hold basic data type classes that all backends need to implement """

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from trail.serialization import to_json
import uuid
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
    uid: Optional[str] = uuid.uuid4()
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Dict[str, any] = field(default_factory=dict)

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

    def to_json(self, short=False):
        return {
            'dtype': 'trial',
            'uid': to_json(self.uid),
            'name': self.name,
            'description': self.description,
            'tags': self.tags,
            'group_id': self.group_id,
            'project_id': self.project_id,
            'parameters': to_json(self.parameters, short),
            'metadata': to_json(self.metadata, short),
            'metrics': to_json(self.metrics, short),
            'chronos': to_json(self.chronos, short),
            'errors': self.errors,
            'status': {
                'value': self.status.value,
                'name': self.status.name
            }
        }

    def __hash__(self):
        return self.uid


@dataclass
class TrialGroup:
    """ Namespace / Set of trials """

    uid: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    trials: List[Trial] = field(default_factory=list)

    project_id: Optional[int] = None

    def to_json(self, short=False):
        return {
            'dtype': 'trial_group',
            'uid': to_json(self.uid),
            'name': self.name,
            'description': self.description,
            'tags': self.tags,
            'project_id': self.project_id,
            'trials': [to_json(t.uid) for t in self.trials]
        }


@dataclass
class Project:
    """ Set of Trial Groups & trials
        If projects define tags than all children inherit those tags.
        children cannot override the tag of a parent
    """

    uid: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    groups: List[TrialGroup] = field(default_factory=list)
    trials: List[Trial] = field(default_factory=list)

    def to_json(self, short=False):
        return {
            'dtype': 'project',
            'uid': to_json(self.uid),
            'name': self.name,
            'description': self.description,
            'tags': self.tags,
            'trials': [to_json(t, short) for t in self.trials],
            'groups': [to_json(g, short) for g in self.groups]
        }


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


