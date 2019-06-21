

class FutureIsNotReady(Exception):
    pass


class Future:
    def __init__(self, promise):
        self.promise = promise

    def get(self):
        return self.promise.returned

    def is_ready(self):
        return self.get() is not None

    def __getattr__(self, item):
        """ if the attribute does not exist we evaluate the partial call and execute that attribute """
        value = self.get()
        if value is None:
            raise FutureIsNotReady()

        return getattr(self.get(), item)


class DelayedCall:
    def __init__(self, fun, kwargs):
        self.fun = fun
        self.kwargs = kwargs
        self.returned = None

    def __call__(self, *args, **kwargs):
        if self.returned is None:
            self.kwargs.update(kwargs)
            self.returned = self.fun(**self.kwargs)
            return self.returned
        else:
            return self.returned(*args, **kwargs)

    def add_arguments(self, **kwargs):
        self.kwargs.update(kwargs)

    def get_future(self):
        return Future(self)

    def __getattr__(self, item):
        """ if the attribute does not exist we evaluate the partial call and execute that attribute """

        if self.returned is None:
            self.returned = self.fun(**self.kwargs)

        return getattr(self.returned, item)


def delay_call(fun, **kwargs):
    return DelayedCall(fun, kwargs)


def is_delayed_call(obj):
    return isinstance(obj, DelayedCall) and obj.returned is None


if __name__ == '__main__':
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
    print(delayed_call(b=2))

    obj = Obj()

    delayed_call2 = delay_call(obj.set, a=2)

    print(delayed_call2)
    print(delayed_call2.get())
