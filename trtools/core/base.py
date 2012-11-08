import pandas as pd

def parallel_apply(func_name, *args):
    """
    """
    d = dict()
    for i, series in enumerate(args):
        name = series.name or 'arg_' + i
        d[name] = series
    df = pd.DataFrame(d, index=args[0].index)
    func = getattr(df, func_name)
    return func(axis=1)

def pmax(*args, **kwargs):
    return parallel_apply('max', *args)

def pmin(*args, **kwargs):
    return parallel_apply('min', *args)
