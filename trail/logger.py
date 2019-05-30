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


class Logger:
    def __init__(self, trial: Trial, backend=None):
        self.trial = trial
        acc = ValueAggregator()
        self.depth = 0
        self.parent_chrono = ChronoContext('runtime', acc, None, self)
        self.start()
        self.backend = backend

    def log_value(self, key: str, value: any, aggregator: Callable[[], Aggregator] = ring_aggregator):
        storage = self.trial.values
        agg = storage.get(key)

        if agg is None:
            agg = aggregator()
            storage[key] = agg

        agg.append(value)

    def log_argument(self, name, key):
        self.trial.args[name] = key

    def log_arguments(self, args: Namespace):
        self.trial.args.update(dict(**vars(args)))

    def _make_container(self, step, aggregator):
        if step is None:
            if aggregator is None:
                # favor ts aggregator because it has an option to cut the TS for printing purposes
                return ts_aggregator()
            return aggregator()
        else:
            return {}

    def log_metrics(self, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwarg):
        """
            :params step optional key that optionally can be set; originally meant as a way to specify a kind of
                    id representing at which step of the training process the model is at.

            :params aggregator: custom container used to store the metrics. if not specified it will fall back
                    to standard `list` and `dict`

            :params kwargs: key, value pair representing the metrics that need to be logged
        """

        for k, v in kwarg.items():
            container = self.trial.metrics.get(k)

            if container is None:
                container = self._make_container(step, aggregator)
                self.trial.metrics[k] = container

            if step and isinstance(container, dict):
                container[step] = v
            elif step:
                container.append((step, v))
            else:
                container.append(v)

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