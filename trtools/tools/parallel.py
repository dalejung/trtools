import multiprocessing as mp

default_consumers = mp.cpu_count() * 2 

def farm(tasks, num_consumers=None, verbose=False):
    if num_consumers is None:
        num_consumers = default_consumers
    task_queue = mp.JoinableQueue()
    result_queue = mp.Queue()

    # Start consumers
    print 'Creating %d consumers' % num_consumers
    consumers = [ DataProcess(task_queue, result_queue, verbose)
                  for i in xrange(num_consumers) ]

    num_jobs = len(tasks)
    print 'Creating Task Queue %d items' % num_jobs
    # fill queue
    for task in tasks:
        task_queue.put(task)

    start_process(task_queue, consumers)

    # Start printing results
    print 'printing results'
    results = []
    while num_consumers:
        result = result_queue.get()
        if result is None:
            num_consumers -= 1
            continue
        results.append(result)       

    return results

def start_process(task_queue, consumers):

    for w in consumers:
        w.start()

    # Add a poison pill for each consumer
    num_consumers = len(consumers)
    for i in range(num_consumers):
        task_queue.put(None)

    # Wait for the worker to finish
    task_queue.join()

class Task(object):
    def __init__(self, func, job):
        self.func = func
        self.job = job

    def __call__(self):
        return self.func(self.job)

    def __str__(self):
        return "Task("+str(self.job)+")"

class DataProcess(mp.Process):
    def __init__(self, task_queue, result_queue, verbose=False):
        super(DataProcess, self).__init__()
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.current_task = None
        self.jobs_complete = 0

    def run(self):
        while self._process_queue():
            self.jobs_complete += 1
            pass
        print '%s: Exiting' % self.name
        self.result_queue.put(None)
        return

    def _process_queue(self):
        task = self.task_queue.get() # blocking
        self.current_task = task
        if task is None:
            # Poison pill means we should exit
            self.task_queue.task_done()
            return False
        if self.verbose:
            print str(self)+'Processing '+str(task)+' Jobs Complete: '+str(self.jobs_complete)
        data = task()
        self.task_queue.task_done()
        if data is not None:
            print 'put data'
            self.result_queue.put(data)
        return True

