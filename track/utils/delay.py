

class DelayedCall:
    def __init__(self, fun, kwargs):
        self.fun = fun
        self.kwargs = kwargs
        self.returned = None

    def __call__(self, *args, **kwargs):
        if self.returned is None:
            self.kwargs.update(kwargs)
            return self.fun(**self.kwargs)
        else:
            return self.returned(*args, **kwargs)

    def __getattr__(self, item):
        """ if the attribute does not exist we evaluate the partial call and execute that attribute """
        if self.returned is None:
            self.returned = self.fun(**self.kwargs)

        return getattr(self.returned, item)


def delay_call(fun, **kwargs):
    return DelayedCall(fun, kwargs)


def is_delayed_call(obj):
    return isinstance(obj, DelayedCall) and obj.returned is None


