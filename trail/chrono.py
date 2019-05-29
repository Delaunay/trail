from trail.aggregators.aggregator import Aggregator
from typing import Callable
import time


class ChronoContext:
    """
        sync is a function that can be set to make the timer wait before ending.
        This is useful when timing async calls like cuda calls
    """
    def __init__(self, name: str, acc: Aggregator, sync: Callable, parent):
        self.name = name
        self.accumulator = acc
        self.start = 0
        self.sync = sync
        self.parent = parent
        self.depth = None

        if sync is None:
            self.sync = lambda: None

    def __enter__(self):
        # Sync before starting timer to make sure previous work is not timed as well
        self.depth = self.parent.depth
        self.parent.depth += 1
        self.sync()

        self.start = time.time()
        return self.accumulator

    def __exit__(self, exception_type, exc_val, traceback):
        # Sync before ending timer to make sure all the work is accounted for
        self.sync()
        self.end = time.time()

        self.parent.depth -= 1
        if exception_type is None:
            self.accumulator.append(self.end - self.start)
        else:
            raise exception_type
