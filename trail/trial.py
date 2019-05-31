from typing import *

from argparse import Namespace
from collections import defaultdict

from dataclasses import dataclass
from dataclasses import field

from trail.serialization import to_json
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
    # Stores metrics that are

    system_metrics: Dict[str, any] = field(default_factory=dict)
    graph_definition: str = None
    args: Namespace = field(default_factory=dict)

    name: str = None
    version: str = None
    trial_uid: str = None
    code: str = None
    source_file: str = None

    status: Status = None
    errors: List[any] = field(default_factory=list)
    chronos: Dict[str, any] = field(default_factory=dict)
    metrics: Dict[any, Dict[any, any]] = field(default_factory=lambda: defaultdict(dict))
    others: Dict[any, Dict[any, any]] = field(default_factory=lambda: defaultdict(dict))

    def to_json(self, short=False):
        return {
            'name': self.name,
            'version': self.version,
            'arguments': to_json(self.args, short),
            'metrics': to_json(self.metrics, short),
            'others': to_json(self.others, short),
            'chronos': to_json(self.chronos, short),
            'system_metrics': to_json(self.system_metrics, short),
            'status': self.status.value
        }
