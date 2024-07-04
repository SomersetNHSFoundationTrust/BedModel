import itertools


class Unique:
    """
    create a new id counting from 100,000
    """
    def __init__(self):
        self.counter = itertools.count(100000)

    def next_counter(self):
        return next(self.counter)