from track.utils.throttle import throttled
import time


class Inc:
    sum = 0

    def add(self):
        self.sum += 1


def test_throttle_time():
    inc = Inc()
    inc_throttled = throttled(inc.add, every=0.05)

    for i in range(0, 100):
        inc_throttled()
        time.sleep(0.01)

    assert inc.sum == int(0.01 * 100 / 0.05)


def test_throttle_count():
    inc = Inc()
    inc_throttled = throttled(inc.add, throttle=5)

    for i in range(0, 100):
        inc_throttled()

    assert inc.sum == 100 // 5


if __name__ == '__main__':
    test_throttle_time()
    test_throttle_count()
