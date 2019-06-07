from track.aggregators.aggregator import ValueAggregator, TimeSeriesAggregator, RingAggregator, StatAggregator


def test_value_aggregator():
    agg = ValueAggregator()

    for i in range(0, 100):
        agg.append(i)

    assert agg.val == 99


def test_timeseries_aggregator():
    agg = TimeSeriesAggregator()

    for i in range(0, 100):
        agg.append(i)

    assert agg.val == list(range(0, 100))


def test_ring_aggregator():
    agg = RingAggregator(20)

    for i in range(0, 100):
        agg.append(i)

    assert agg.val == list(range(0, 100))[-20:]


def test_stat_aggregator():
    agg = StatAggregator(skip_obs=10)

    for i in range(0, 100):
        agg.append(i)

    assert agg.avg == 54.5
    assert agg.min == 9
    assert agg.max == 99
    assert agg.sd == 25.97915831328387
    assert agg.sum == sum(range(10, 100))


if __name__ == '__main__':

    test_ring_aggregator()
    test_timeseries_aggregator()
    test_value_aggregator()
    test_stat_aggregator()
