import operator

from trtools.tools.processing import ParallelDataProcessor, DataProcessor
from trtools.common import missing

class StoreResultHandler(object):
    """
    A resulthandler that translates a handler(job, data) to a store[job] = data
    call. 

    It also has a store_key func incase you want use a derivative of job as the
    store key
    """
    def __init__(self, store, store_key):
        self.store = store

        if isinstance(store_key, str):
            store_key = operator.attrgetter(store_key)
        if store_key is None:
            store_key = lambda x: x
        self.store_key = store_key

    def __call__(self, job, data):
        key = self.store_key(job)
        self.store[key] = data

class DataPanel(object):
    """
    Should accept a store, which is dict like.
    DataProcessor doesn't have any machinery for data retention, only a result handler

    job_trans is to handle the fact that sometimes jobs are object, but need to 
    be converted into int/strings for data storage

    store_key is if the job needs translation
    """
    def __init__(self, jobs, store=None, mgr=None, job_trans=None, store_key=None, result_handler=missing):
        if job_trans is None:
            job_trans = lambda x: x

        self.job_trans = job_trans
        self.jobs = job_trans(jobs)
        self.mgr = mgr
        self.store = store

        if result_handler == missing:
            result_handler = StoreResultHandler(store, store_key)
        self.handler = result_handler

    def process(self, func, refresh=False, num=None, parallel=True, *args, **kwargs):
        if refresh:  
            self.store.delete_all()

        jobs = self.remaining_jobs()
        if num > 0:
            jobs = jobs[:num]

        processor = self.get_processor(jobs, parallel=parallel)
        processor.process(func, *args, **kwargs)

    def get_processor(self, jobs, parallel=True):
        if parallel:
            processor = ParallelDataProcessor(jobs, result_handler=self.handler, 
                                          mgr=self.mgr)
        else:
            processor = DataProcessor(jobs, result_handler=self.handler, 
                                          mgr=self.mgr)
        return processor

    def remaining_jobs(self):
        done = None
        if hasattr(self.store, 'keys'):
            done = self.job_trans(list(self.store.keys())) # most stores will enforce int/str
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
