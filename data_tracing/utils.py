import itertools as it


def pairwise(iterable):
    """
    Copied from the python 3.10 itertools library
    :param iterable:
    :return:
    """
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = it.tee(iterable)
    next(b, None)
    return zip(a, b)
