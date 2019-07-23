import array


class RingBuffer:
    def __init__(self, size, dtype, default_val=0):
        if len(str(dtype)) > 1:
            self.array = [default_val] * size
        else:
            self.array = array.array(dtype, [default_val] * size)

        self.capacity = size
        self.offset = 0

    def __getitem__(self, item):
        return self.array[item % self.capacity]

    def __setitem__(self, item, value):
        self.array[item % self.capacity] = value

    def append(self, item):
        self.array[self.offset % self.capacity] = item
        self.offset += 1

    def to_list(self):
        if self.offset < self.capacity:
            return list(self.array[:self.offset])
        else:
            end_idx = self.offset % self.capacity
            return list(self.array[end_idx: self.capacity]) + list(self.array[0:end_idx])

    def __len__(self):
        return min(self.capacity, self.offset)

    def last(self):
        if self.offset == 0:
            return None

        return self.array[(self.offset - 1) % self.capacity]

