from trail.containers.ring import RingBuffer
from trail.containers.types import float32
from benchutils.statstream import StatStream


class Aggregator:
    def __init__(self, logger=None):
        self.logger = logger

    def append(self, other):
        raise NotImplementedError()

    def __iadd__(self, other):
        return self.append(other)

    @property
    def val(self):
        """ Return the last observed value """
        raise NotImplementedError()

    def to_json(self, short=False):
        raise NotImplementedError()

    @staticmethod
    def lazy(aggregator_t, **kwargs):
        """Lazily instantiate the underlying aggregator """
        raise lambda: aggregator_t(**kwargs)


class RingAggregator(Aggregator):
    """ Saves the `n` last elements. Start overriding the elements once `n` elements is reached """

    def __init__(self, n, dtype=float32):
        self.ring = RingBuffer(n, dtype)

    def append(self, other):
        self.ring.append(other)

    @property
    def val(self):
        return self.ring.last()

    @staticmethod
    def lazy(n, dtype):
        return lambda: RingAggregator(n, dtype)

    def to_json(self, short=False):
        return self.ring.to_list()


class StatAggregator(Aggregator):
    """ Compute mean, sd, min, max; does not keep the entire history.
        This is useful if you are worried about memory usage and the values should not vary much.
        i.e keeping the entire history is not useful.
    """

    def __init__(self, skip_obs=10):
        self.stat = StatStream(drop_first_obs=skip_obs)

    def append(self, other):
        self.stat.update(other)

    @property
    def val(self):
        return self.stat.val

    @staticmethod
    def lazy(skip):
        return lambda: StatAggregator(skip)

    def to_json(self, short=False):
        return self.stat.to_dict()

    @property
    def avg(self):
        return self.stat.avg


class TimeSeriesAggregator(Aggregator):
    """ Keeps the entire history of the metric """

    def __init__(self):
        self.time_series = []

    def append(self, other):
        self.time_series.append(other)

    @property
    def val(self):
        return self.time_series[-1]

    @staticmethod
    def lazy():
        return lambda: TimeSeriesAggregator()

    def to_json(self, short=False):
        if short:
            return self.time_series[-20:]
        return self.time_series


class ValueAggregator(Aggregator):
    """ Does not Aggregate only keeps the latest value """

    def __init__(self):
        self.value = None

    def append(self, other):
        self.value = other

    @property
    def val(self):
        return self.value

    @staticmethod
    def lazy():
        return lambda: ValueAggregator()

    def to_json(self, short=False):
        return self.value


def aggregate(agg, value):
    if agg.logger is None:
        return agg.append(value)
    agg.append(value)
