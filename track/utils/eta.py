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


def to_list(item):
    try:
        return list(item)
    except Exception:
        return [item]


class EstimatedTime:
    """
        eta = EstimatedTime(timer, (total_epoch, batch_per_epoch))

        eta.estimate_time((1, 2)

    """
    def __init__(self, stat_timer: StatStream, total: Union[int, List[int]], start: int = 0, name: str = None):
        self.offset = 1 - start
        self.timer = stat_timer
        self.totals = to_list(total)
        self.last_step = None
        self.name = name

    def set_totals(self, t):
        """ set the total number of iteration for each step"""
        self.totals = to_list(t)

    @property
    def total(self):
        return self.count(self.totals)

    @staticmethod
    def count(item, offset=0):
        """ return the current iteration it given the completion of each steps """
        total = item
        if isinstance(item, list):
            total = 1

            for i in item:
                total *= (i + offset)

        return total

    def estimated_time(self, step: int, unit: int = minutes):
        """ estimate the time remaining before the end of the computation """
        self.last_step = step
        return get_time(self.timer) * (self.total - self.count(step, self.offset)) / unit

    def elapsed(self, unit: int = minutes):
        """ return the elapsed time since the class was created"""
        return self.timer.total / unit

    def show_eta(self, step, msg='', show=True):
        """ print the estimate time until the processing is done """
        step = to_list(step)
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
