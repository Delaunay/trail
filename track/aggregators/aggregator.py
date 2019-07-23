from track.containers.ring import RingBuffer
from track.containers.types import float32
from track.utils.stat import StatStream


class Aggregator:
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
        return lambda: aggregator_t(**kwargs)


class RingAggregator(Aggregator):
    """ Saves the `n` last elements. Start overriding the elements once `n` elements is reached """

    def __init__(self, n, dtype=float32):
        self.ring = RingBuffer(n, dtype)

    def append(self, other):
        self.ring.append(other)

    @property
    def val(self):
        return self.ring.to_list()

    @staticmethod
    def lazy(n, dtype):
        return lambda: RingAggregator(n, dtype)

    def to_json(self, short=False):
        return self.ring.to_list()

    def __repr__(self):
        return f'r<{repr(self.ring.to_list())}>'

    def __str__(self):
        return f'r<{str(self.ring.to_list())}>'


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

    @property
    def max(self):
        return self.stat.max

    @property
    def min(self):
        return self.stat.min

    @property
    def sd(self):
        return self.stat.sd

    @property
    def sum(self):
        return self.stat.total

    @property
    def total(self):
        return self.stat.total

    def __repr__(self):
        return f's<{repr(self.stat.to_dict())}>'

    def __str__(self):
        return f's<{str(self.stat.to_dict())}>'


class TimeSeriesAggregator(Aggregator):
    """ Keeps the entire history of the metric """

    def __init__(self):
        self.time_series = []

    def append(self, other):
        self.time_series.append(other)

    @property
    def val(self):
        return self.time_series

    @staticmethod
    def lazy():
        return lambda: TimeSeriesAggregator()

    def to_json(self, short=False):
        if short:
            return self.time_series[-20:]
        return self.time_series

    def __repr__(self):
        return f'ts<{repr(self.time_series)}>'

    def __str__(self):
        return f'ts<{str(self.time_series)}>'


class ValueAggregator(Aggregator):
    """ Does not Aggregate only keeps the latest value """

    def __init__(self, val=None):
        self.value = val

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

    def __repr__(self):
        return f'v<{repr(self.value)}>'

    def __str__(self):
        return f'v<{str(self.value)}>'
