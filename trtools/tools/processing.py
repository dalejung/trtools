import trtools.tools.parallel as parallel

from trtools.common import missing

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
            print("Error: job: {0} {1}".format(self.job, str(e)))
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
        tasks = self.generate_tasks(func, batch)
        result_handler = self.result_handler
        for task in tasks:
            job, data = task()
            if result_handler:
                result_handler(job, data)
        return result_handler

    def generate_tasks(self, func, batch):
        tasks = [DataPanelTask(func, job, self.mgr) for job in batch]
        return tasks

    def __getstate__(self): return self.__dict__
    def __setstate__(self, d): self.__dict__.update(d)

class ParallelDataProcessor(DataProcessor):

    def process(self, func=None, *args, **kwargs):
        batch = self.jobs
        return self.process_parallel(batch, func, *args, **kwargs)

    def process_parallel(self, batch, func, num_consumers=None, verbose=False, process_vars=None):
        tasks = self.generate_tasks(func, batch)
        result_wrap = result_handler = self.result_handler
        if result_handler:
            # split up here so we don't have to job, data = result
            result_wrap = lambda result: result_handler(result[0], result[1])

        parallel.farm(tasks, num_consumers=num_consumers, verbose=verbose,
                            result_handler=result_wrap, process_vars=process_vars)
        return result_handler

    def result_wrapper(self, result):
        """
            Just splits result in job / data
        """
        job, data = result
        return self.result_handler(job, data)

def process_jobs(jobs, func, mgr, result_handler=missing):
    dp = ParallelDataProcessor(jobs, mgr=mgr, result_handler=result_handler)
    return dp.process(func)


