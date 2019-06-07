from benchutils.statstream import StatStream
from typing import Union, List
from math import log10


def get_time(time: StatStream):
    avg = time.avg
    if avg == 0:
        return time.val
    return avg


seconds = 1
minutes = 60


class EstimatedTime:
    """
        eta = EstimatedTime(timer, (total_epoch, batch_per_epoch))

        eta.estimate_time((1, 2)

    """
    def __init__(self, stat_timer: StatStream, total: Union[int, List[int]], start: int = 0, name: str = None):
        self.offset = 1 - start
        self.timer = stat_timer
        self.totals = self.to_list(total)
        self.last_step = None
        self.name = name

    def set_totals(self, t):
        self.totals = self.to_list(t)

    @property
    def total(self):
        return self.count(self.totals)

    def count(self, item, offset=0):
        total = item
        if isinstance(item, list):
            total = 1

            for i in item:
                total *= (i + offset)

        return total

    def to_list(self, item):
        try:
            return list(item)
        except Exception:
            return [item]

    def estimated_time(self, step: int, unit: int = minutes):
        self.last_step = step
        return get_time(self.timer) * (self.total - self.count(step, self.offset)) / unit

    def elapsed(self, unit: int = minutes):
        return self.timer.total / unit

    def show_eta(self, step, msg='', show=True):
        step = self.to_list(step)
        was_changed = False

        diff = len(step) - len(self.totals)
        for _ in range(diff):
            self.totals.append(1)

        msgs = []
        for idx, (i, total) in enumerate(zip(step, self.totals)):
            size = int(log10(total)) + 1
            # inference of the size
            self.totals[idx] = max(i + self.offset, total, self.totals[idx])

            if total != self.totals[idx]:
                total = self.totals[idx]
                was_changed = True

            msgs.append(f'[{i + self.offset:{size}d}/{total:{size}d}]')

        if was_changed:
            msgs.append(' | Elapsed ')
            if self.name:
                msgs.append(self.name)
            msgs.append(f' {self.elapsed():8.2f} min')

        else:
            msgs.append(f' | ETA ')
            if self.name:
                msgs.append(self.name)

            msgs.append(f' {self.estimated_time(step, minutes):8.2f} min ')

        msgs.append(msg)
        msg = ''.join(msgs)
        if show:
            return print(msg)
        return msg


if __name__ == '__main__':
    import time
    from track.chrono import ChronoContext
    from track.aggregators.aggregator import StatAggregator

    agg = StatAggregator()
    eta = EstimatedTime(agg, (5, 1))

    print(eta.total)

    for i in range(0, 5):
        for j in range(0, 10):

            with ChronoContext('time', agg, None, None):
                time.sleep(1)

        eta.show_eta((i, j))

    agg = StatAggregator()
    eta = EstimatedTime(agg, 50)

    print(eta.total)

    for i in range(50):

        with ChronoContext('time', agg, None, None):
            time.sleep(1)

        eta.show_eta(i)
