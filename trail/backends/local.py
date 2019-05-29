from argparse import Namespace
from typing import Callable

from trail.containers.types import float32
from trail.trial import Trial

from trail.chrono import ChronoContext
from trail.aggregators.aggregator import Aggregator
from trail.aggregators.aggregator import RingAggregator
from trail.aggregators.aggregator import StatAggregator
from trail.aggregators.aggregator import ValueAggregator
from trail.aggregators.aggregator import TimeSeriesAggregator


ring_aggregator = RingAggregator.lazy(10, float32)
stat_aggregator = StatAggregator.lazy(1)
ts_aggregator = TimeSeriesAggregator.lazy()
current_trial = None
current_logger = None


class Logger:
    def __init__(self, trial: Trial):
        self.trial = trial
        acc = ValueAggregator()
        self.depth = 0
        self.parent_chrono = ChronoContext('runtime', acc, None, self)
        self.start()

    def log_value(self, key: str, value: any, aggregator: Callable[[], Aggregator] = ring_aggregator):
        storage = self.trial.values
        agg = storage.get(key)

        if agg is None:
            agg = aggregator()
            storage[key] = agg

        agg.append(value)

    def log_arguments(self, args: Namespace):
        self.trial.args = args

    def log_metric(self, step: any, **kwargs):
        self.trial.metrics[step].update(kwargs)

    def log_metrics(self, step: any = None, aggregator: Callable[[], Aggregator] = ring_aggregator, **kwargs):
        if step is None:
            for k, v in kwargs.items():
                self.log_value(k, v, aggregator)
        else:
            self.log_metric(step, **kwargs)

    def chrono(self, name: str, aggregator: Callable[[], Aggregator] = stat_aggregator, sync=None):
        """ create a chrono context to time the runtime of the code inside it"""
        agg = self.trial.values.get(name)
        if agg is None:
            agg = aggregator()
            self.trial.values[name] = agg

        return ChronoContext(name, agg, sync, self.parent_chrono)

    # Context API for starting the top level chrono
    def finish(self):
        self.parent_chrono.__exit__(None, None, None)

    def start(self):
        self.parent_chrono.__enter__()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.parent_chrono.__exit__(exc_type, exc_val, exc_tb)