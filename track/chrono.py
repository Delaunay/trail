from track.aggregators.aggregator import Aggregator
from typing import Callable
import time


class ChronoContext:
    """
        sync is a function that can be set to make the timer wait before ending.
        This is useful when timing async calls like cuda calls
    """
    def __init__(self, name: str, acc: Aggregator, stat_callback: Callable = None, end_callback: Callable = None):
        self.name = name
        self.accumulator = acc
        self.start = 0
        self.end = 0
        self.start_callback = stat_callback
        self.end_callback = end_callback

        if stat_callback is None:
            self.stat_callback = lambda: None

        if end_callback is None:
            self.end_callback = lambda: None

    def __enter__(self):
        self.start_callback()
        self.start = time.time()
        return self.accumulator

    def __exit__(self, exception_type, exc_val, traceback):
        # Sync before ending timer to make sure all the work is accounted for
        self.end_callback()
        self.end = time.time()

        if exception_type is None:
            self.accumulator.append(self.end - self.start)
        else:
            raise exception_type
