

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
        self.is_processing = False

    def __call__(self, *args, **kwargs):
        if self.returned is None and self.is_processing:
            raise RuntimeError('Circular dependencies')

        if self.returned is None:
            self.kwargs.update(kwargs)
            self.is_processing = True
            self.returned = self.fun(**self.kwargs)
            self.is_processing = False
            return self.returned
        else:
            return self.returned(*args, **kwargs)

    def add_arguments(self, **kwargs):
        self.kwargs.update(kwargs)

    def get_future(self):
        return Future(self)

    def __getattr__(self, item):
        """ if the attribute does not exist we evaluate the partial call and execute that attribute """

        if self.returned is None and self.is_processing:
            raise RuntimeError('Circular dependencies')

        if self.returned is None:
            self.is_processing = True
            self.returned = self.fun(**self.kwargs)
            self.is_processing = False

        return getattr(self.returned, item)


def delay_call(fun, **kwargs):
    return DelayedCall(fun, kwargs)


def is_delayed_call(obj):
    return isinstance(obj, DelayedCall) and obj.returned is None


