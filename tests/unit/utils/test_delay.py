from track.utils.delay import delay_call, is_delayed_call


def test_delay():
    class Obj:
        a = 0
        b = 0

        def set(self, a=0, b=0):
            self.a = a
            self.b = b
            return self

        def get(self):
            return self.a + self.b

    def add(a, b):
        return a + b

    delayed_call = delay_call(add, a=2)
    assert delayed_call(b=2) == 4

    obj = Obj()

    delayed_call2 = delay_call(obj.set, a=2)

    assert is_delayed_call(delayed_call2)
    assert delayed_call2.get() == 2


if __name__ == '__main__':
    test_delay()
