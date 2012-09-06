import trtools.tools.parallel as parallel 
import operator

import pandas as pd

class DataPanelTask(parallel.Task):
    """
        mgr - callable that returns data to be processed by func
    """
    def __init__(self, func, job, mgr=None, post_func=None):
        self.func = func
        self.job = job
        self.mgr = mgr
        self.post_func = post_func

    def __call__(self):
        try:
            result = self.run_job()
        except Exception as e:
            result = (self.job, None)
            print "Error: job: {0} {1}".format(self.job, str(e))
        return result

    def run_job(self):
        data = self.job
        if self.mgr:
            data = self.mgr(self.job)
        result = (self.job, self.func(data))

        if self.post_func:
            result = self.post_func(result)
        return result

    def __repr__(self):
        return "Task(job={0}, mgr={1})".format(str(self.job), str(self.mgr))

class AggregateResultStore(object):
    """
        Default Aggregate store that basically acts like a dict.
    """
    def __init__(self):
        self.results = {}

    def __call__(self, job, data):
        self.results[job] = data

missing = object() # sentinel since None is valid input
class DataProcessor(object):
    """
        The basic idea is we setup a DataProcessor which is a mgr and jobs
        In finance data that would be something like EOD and a list of symbols

        Note: mgr is really just a callable, so if your data/process step can be
        better expressed in one function, DataPanel supports not calling the mgr
    """
    def __init__(self, jobs=None, mgr=None, result_handler=missing):
        self.mgr = mgr
        self.jobs = jobs

        if result_handler is missing:
            result_handler = AggregateResultStore()
        self.result_handler = result_handler

    def add_jobs(self, new_jobs):
        self.jobs.extend(new_jobs)

    def process(self, func=None, *args, **kwargs):
        wrap_func = func
        if isinstance(func, basestring): # easy support of calling methods on data
            wrap_func = lambda df: getattr(df, func)()
            
        batch = self.jobs
        return self._process(batch, wrap_func, *args, **kwargs)

    def _process(self, batch, func, *args, **kwargs):
        tasks = [DataPanelTask(func, job, self.mgr) for job in batch]
        result_handler = self.result_handler
        for task in tasks:
            job, data = task()
            if result_handler:
                result_handler(job, data)
        return result_handler

    def process_job(self, job, func):
        data = job
        if self.mgr:
            data = self.mgr(job)
        return (job, func(data))

    def __getstate__(self): return self.__dict__
    def __setstate__(self, d): self.__dict__.update(d)

class ParallelDataProcessor(DataProcessor):
    def process(self, func=None, *args, **kwargs):
        batch = self.jobs
        return self.process_parallel(batch, func, *args, **kwargs)

    def process_parallel(self, batch, func, num_consumers=8, verbose=False):
        tasks = [DataPanelTask(func, job, self.mgr) for job in batch]
        result_wrap = result_handler = self.result_handler
        if result_handler:
            result_wrap = lambda result: result_handler(result[0], result[1])

        parallel.farm(tasks, num_consumers=num_consumers, verbose=verbose, 
                            result_handler=result_wrap)
        return result_handler

    def result_wrapper(self, result):
        """
            Just splits result in job / data
        """
        job, data = result
        return self.result_handler(job, data)

class DataPanel(object):
    """
    Should accept a store, which is dict like.
    DataProcessor doesn't have any machinery for data retention, only a result handler

    job_trans is to handle the fact that sometimes jobs are object, but need to 
    be converted into int/strings for data storage

    store_key is if the job needs translation
    """
    def __init__(self, jobs, store, mgr=None, job_trans=None, store_key=None):
        if job_trans is None:
            job_trans = lambda x: x

        self.job_trans = job_trans
        self.store = store
        self.jobs = job_trans(jobs)
        if isinstance(store_key, basestring):
            store_key = operator.attrgetter(store_key)
        if store_key is None:
            store_key = lambda x: x
        self.store_key = store_key

        self.mgr = mgr

    def handler(self, job, result):
        key = self.store_key(job)
        self.store[key] = result

    def process(self, func, refresh=False, num=None, *args, **kwargs):
        if refresh:  
            self.store.delete_all()

        jobs = self.remaining_jobs()
        if num > 0:
            jobs = jobs[:num]

        processor = ParallelDataProcessor(jobs, result_handler=self.handler, 
                                          mgr=self.mgr)
        processor.process(func, *args, **kwargs)

    def remaining_jobs(self):
        done = self.job_trans(self.store.keys()) # most stores will enforce int/str
        if not done:
            return self.jobs

        remaining = set(self.jobs).difference(set(done))
        return list(remaining)

    def __getitem__(self, key):
        return self.store[key]

    @property
    def sql(self):
        return self.store.sql

    def close(self):
        self.store.close()
