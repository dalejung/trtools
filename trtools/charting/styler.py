import itertools

def styler():
    linestyles = ['-', '--', ':']
    colors = ('b', 'g', 'r', 'c', 'm', 'y', 'k')

    styles = itertools.product(linestyles, colors)

    while True:
        yield dict(zip(('linestyle', 'color'), styles.next()))

def marker_styler():
    """
    Adds differing markers
    """
    linestyles = ['-', '--', ':']
    colors = ('b', 'g', 'r', 'c', 'm', 'y', 'k')

    styles = itertools.product(linestyles, colors)

    while True:
        yield dict(zip(('linestyle', 'color'), styles.next()))
