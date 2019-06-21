

class PartialCall:
    def __init__(self, fun, kwargs):
        self.fun = fun
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        self.kwargs.update(kwargs)
        self.fun(**self.kwargs)


def partial(fun, **kwargs):
    return PartialCall(fun, kwargs)

