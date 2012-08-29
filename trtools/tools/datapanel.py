import trtools.tools.parallel as parallel 
import cPickle as pickle

class Wrap(object):
    def __init__(self, func, mgr=None):
        self.func = func
        self.mgr = mgr

    def __call__(self, job):
        df = self.mgr(job)
        return (job, self.func(df))

    def __getstate__(self): return self.__dict__
    def __setstate__(self, d): self.__dict__.update(d)

class DataPanel(object):
    def __init__(self, mgr, stocks):
        self.mgr = mgr
        self.stocks = stocks

    def get_data(self, stock):
        return self.mgr(stock)

    def __getattr__(self, name):
        df = self.get_data(self.stocks[0])
        if hasattr(df, name):
            return getattr(df, name)
        raise AttributeError("Attribute not found")

    def __getstate__(self): return self.__dict__
    def __setstate__(self, d): self.__dict__.update(d)

    def process(self, func, test=True):
        batch = self.stocks
        if test:
            batch = batch[:5]

        wrap_func = func
        if isinstance(func, basestring):
            wrap_func = lambda df: getattr(df, func)()
            
        return self.process_parallel(batch, wrap_func)

    def _process(self, batch, func):
        results = {}
        for job in batch:
            results[job] = self.process_job(job, func)[1]

        return results

    def process_job(self, job, func):
        df = self.get_data(job)
        return (job, func(df))

    def process_parallel(self, func, num_consumers=8, verbose=False):
        batch = self.stocks
        tasks = [parallel.Task(Wrap(func, self.mgr), job) for job in batch]
        res = parallel.farm(tasks, num_consumers=num_consumers, verbose=verbose)
        return dict(res)
