from track.utils.eta import EstimatedTime


if __name__ == '__main__':
    import time
    from track.chrono import ChronoContext
    from track.aggregators.aggregator import StatAggregator

    agg = StatAggregator()
    eta = EstimatedTime(agg, (5, 1))

    print(eta.total)

    for i in range(0, 5):
        for j in range(0, 10):

            with ChronoContext(agg, None, None):
                time.sleep(1)

        eta.show_eta((i, j))

    agg = StatAggregator()
    eta = EstimatedTime(agg, 50)

    print(eta.total)

    for i in range(50):

        with ChronoContext(agg, None, None):
            time.sleep(1)

        eta.show_eta(i)
