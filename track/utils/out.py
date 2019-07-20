from track.containers.ring import RingBuffer


class RingOutputDecorator:
    def __init__(self, file=None, n_entries=50):
        self.file = file
        self.entries = RingBuffer(n_entries, dtype=str)

    def write(self, string):
        self.entries.append(string)
        if self.file:
            self.file.write(string)

    def out(self):
        return ''.join(self.entries.to_list())

    def flush(self):
        pass

    def output(self):
        return ''.join(self.entries.to_list())

    def raw(self):
        return self.entries.to_list()
