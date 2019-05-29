import json
from typing import *

from argparse import Namespace

from dataclasses import dataclass
from dataclasses import field

from trail.aggregators.aggregator import Aggregator
from trail.aggregators.aggregator import RingAggregator
from trail.aggregators.aggregator import StatAggregator
from trail.aggregators.aggregator import ValueAggregator

from trail.containers.types import float32
from trail.chrono import ChronoContext


def to_json(k: any, short=False):
    if hasattr(k, 'to_json'):
        try:
            return k.to_json(short)
        except TypeError as e:
            print(type(k))
            raise e
    return k


@dataclass
class Trial:
    # Stores metrics that are
    metrics: Dict[str, any] = field(default_factory=dict)
    args: Namespace = None

    def to_json(self, short=False):
        return {
            'metrics': {k: to_json(v, short) for k, v in self.metrics.items()}
        }


# Aggregator.lazy(RingAggregator, 10, float32)
ring_aggregator = RingAggregator.lazy(10, float32)
stat_aggregator = StatAggregator.lazy(1)
current_trial = None
current_logger = None


def get_current_trial():
    return current_trial


def get_current_logger():
    return current_logger


class TrialLogger:
    def __init__(self, trial=None):
        global current_trial
        global current_logger

        if trial is None:
            trial = Trial()

        self.trial = trial
        current_trial = trial
        current_logger = self

        # Top level Chrono
        self.depth = 0
        acc = ValueAggregator()
        self.parent_chrono = ChronoContext('runtime', acc, None, self)
        self.trial.metrics['runtime'] = acc

        self.log_backend: BaseLogger = None

    def finish(self):
        self.parent_chrono.__exit__(None, None, None)

    def start(self):
        self.parent_chrono.__enter__()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.parent_chrono.__exit__(exc_type, exc_val, exc_tb)

    def log_metric(self, name: str, val: any, aggregator: Callable[[], Aggregator] = ring_aggregator):
        """
        :param name of the metric that is being logged
        :param val value of the metric
        :param aggregator how each metric should be aggregated over
        :return:
        """
        agg = self.trial.metrics.get(name)
        if agg is None:
            agg = aggregator()
            self.trial.metrics[name] = agg

        agg.append(val)
        if self.log_backend is not None:
            self.log_backend.log_metric(name, val)

    def chrono(self, name: str, aggregator: Callable[[], Aggregator] = stat_aggregator, sync=None):
        agg = self.trial.metrics.get(name)
        if agg is None:
            agg = aggregator()
            self.trial.metrics[name] = agg

        return ChronoContext(name, agg, sync, self.parent_chrono)


def report(trial: TrialLogger):
    print(json.dumps(trial.trial.to_json(), indent=2))


if __name__ == '__main__':
    import time

    # Explicit API
    exp = Experience(
        'checking_stuffout',
        'hyper-param-space'
    )

    with exp.trial('checking', 'hyper-param', 'params') as logger:

        for epoch in range(0, 5):
            with logger.chrono('epoch_time', StatAggregator.lazy(skip=1)):

                for batch in range(0, 10):
                    with logger.chrono('batch_time', StatAggregator.lazy(skip=10)):

                        time.sleep(1)
                        logger.log_metric('loss', 10, stat_aggregator)

    report(logger)

    with exp.trial('checking', 'hyper-param', 'params') as logger:

        for epoch in range(0, 5):
            with logger.chrono('epoch_time', StatAggregator.lazy(skip=1)):

                for batch in range(0, 10):
                    with logger.chrono('batch_time', StatAggregator.lazy(skip=10)):
                        time.sleep(1)
                        logger.log_metric('loss', 10, stat_aggregator)

    report(logger)

    report(exp)

    # Implicit API - Comet ML
    # One Experience is also one Trial
    exp = Experience(
        'checking_stuffout',
        'hyper-param', 'params'
    )

    for epoch in range(0, 5):
        with exp.chrono('epoch_time', StatAggregator.lazy(skip=1)):

            for batch in range(0, 10):
                with exp.chrono('batch_time', StatAggregator.lazy(skip=10)):
                    time.sleep(1)
                    exp.log_metric('loss', 10, stat_aggregator)