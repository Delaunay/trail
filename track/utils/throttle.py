import time
from typing import Callable, TypeVar, Optional

A = TypeVar('A')  # Arguments
R = TypeVar('R')  # Return Type


class Throttler:
    """ Limit how often the function `fun` is called by calling it only every `throttle` time it has been called """

    def __init__(self, fun: Callable[[A], R], throttle=1):
        self.fun = fun
        self.throttle = throttle
        self.count = 0

    def __call__(self, *args, **kwargs) -> Optional[R]:
        self.count += 1

        if self.count == 1:
            return self.fun(*args, **kwargs)

        else:
            self.count %= self.throttle
            return None


class TimeThrottler:
    """ Limit how often the function `fun` is called in seconds """
    def __init__(self, fun: Callable[[A], R], every=10):
        self.fun = fun
        self.last_time = 0
        self.every = every

    def __call__(self, *args, **kwargs) -> Optional[R]:
        now = time.time()
        elapsed = now - self.last_time

        if elapsed > self.every:
            self.last_time = now
            return self.fun(*args, **kwargs)

        return None


def throttled(fun: Callable[[A], R], throttle=None, every=None) -> Callable[[A], Optional[R]]:
    if throttle is None and every is None:
        return fun
    elif every is None:
        return Throttler(fun, throttle)
    else:
        return TimeThrottler(fun, every)


def is_throttled(fun: Callable[[A], R]) -> bool:
    return isinstance(fun, (TimeThrottler, Throttler))


if __name__ == '__main__':

    base_fun = lambda x: print(x)

    # ---
    fun = throttled(base_fun, throttle=10)
    for i in range(0, 20):
        fun(i)
    print(is_throttled(fun))

    # ---
    fun = throttled(base_fun, every=2)
    for i in range(0, 10):
        fun(i)
        time.sleep(1)

    print(is_throttled(fun))

