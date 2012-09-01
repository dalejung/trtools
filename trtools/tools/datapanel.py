import trtools.tools.parallel as parallel 
import cPickle as pickle
from functools import partial

class DataPanelTask(parallel.Task):
    """
    """
    def __init__(self, func, job, mgr):
        self.mgr = mgr
        self.func = func
        self.job = job

    def __call__(self):
        df = self.mgr(self.job)
        return (self.job, self.func(df))

    def __repr__(self):
        return "Task(job={0}, mgr={1})".format(str(self.job), str(self.mgr))

class AggregateResultStore(object):
    """
        Default Aggregate store that basically acts like a dict.
    """
    def __init__(self):
        self.results = {}

    def __call__(self, result):
        for job, data in result:
            self.results[job] = data


class DataPanel(object):
    def __init__(self, mgr, stocks, store=None):
        self.mgr = mgr
        self.stocks = stocks
        self.store = store or AggregateResultStore()

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
        tasks = [DataPanelTask(func, job, self.mgr) for job in batch]
        res = parallel.farm(tasks, num_consumers=num_consumers, verbose=verbose, 
                            result_handler=self.store)
        return res
