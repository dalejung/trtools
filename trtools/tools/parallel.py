import multiprocessing as mp
import math
import datetime

default_consumers = mp.cpu_count() * 2

def chunker(seq, size):
        return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))

# OSX Max Queue Size
MAX_SIZE = 32000

class ResultHandler(object):
    """ Default result handler """
    def __init__(self):
        self.results = []

    def __call__(self, result):
        self.results.append(result)


missing = object() # sentinel since None is valid input
def farm(tasks, num_consumers=None, verbose=False, result_handler=missing, process_vars=None):
    if result_handler is missing:
        result_handler = ResultHandler()
    if num_consumers is None:
        num_consumers = default_consumers
    task_queue = mp.Queue()
    result_queue = mp.Queue()

    print(result_handler)

    # Start consumers
    print(('Starting farming tasks at:{time}'.format(time=datetime.datetime.now())))
    print(('Creating %d consumers' % num_consumers))
    consumers = [ DataProcess(task_queue, result_queue, verbose=verbose,
                              process_vars=process_vars)
                  for i in xrange(num_consumers) ]

    num_jobs = len(tasks)
    print(('Creating Task Queue %d items' % num_jobs))
    # fill queue

    if len(tasks) > MAX_SIZE:
        tasks = chunker(tasks, int(math.ceil(len(tasks)*1.0/MAX_SIZE)))
    else:
        tasks = chunker(tasks, 1)

    for task in tasks:
        task_queue.put(task, False)

    print('starting process')
    start_process(task_queue, consumers)

    # Start printing results
    jobs_processed = 0
    bins = num_jobs // 20
    bins = max(bins, 1)
    while num_consumers:
        result = result_queue.get()
        if result is None:
            num_consumers -= 1
            continue
        # We send jobs in batches.
        # call result_handler independently to hide implementation from
        # client
        for r in result:
            if result_handler is not None:
                result_handler(r)
            jobs_processed += 1
            if jobs_processed % bins == 0:
                print(("{0} jobs processed".format(jobs_processed)))

    return result_handler

def start_process(task_queue, consumers):

    for w in consumers:
        w.start()

    # Add a poison pill for each consumer
    num_consumers = len(consumers)
    for i in range(num_consumers):
        task_queue.put(None)

    # Wait for the worker to finish
    #task_queue.join()

class Task(object):
    def __init__(self, func, job):
        self.func = func
        self.job = job

    def __call__(self):
        return self.func(self.job)

    def __str__(self):
        return "Task("+str(self.job)+")"

class DataProcess(mp.Process):
    def __init__(self, task_queue, result_queue, verbose=False, process_vars=None):
        super(DataProcess, self).__init__()
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.current_task = None
        self.jobs_complete = 0
        self.verbose = verbose
        if process_vars:
            for k, v in process_vars.items():
                setattr(self, k, v)

    def run(self):
        while self._process_queue():
            self.jobs_complete += 1
            pass
        print(('%s: Exiting' % self.name))
        self.result_queue.put(None)
        return

    def _process_queue(self):
        task = self.task_queue.get() # blocking
        self.current_task = task
        if task is None:
            # Poison pill means we should exit
            return False
        if self.verbose:
            print((str(self)+'Processing '+str(task)+' Jobs Complete: '+str(self.jobs_complete)))

        data = []
        for t in task:
            d = t()
            if d is not None:
                data.append(d)
        if len(data) > 0:
            self.result_queue.put(data)
        return True

