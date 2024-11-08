from dataclasses import dataclass, field
from enum import Enum
from typing import List, Callable, Dict, Tuple, Optional, ClassVar, Type
import time
import traceback
import threading
from threading import Thread, Lock, Event
from ClassyFlaskDB.DefaultModel import *
from AbstractAI.Helpers.Signal import Signal

class JobPriority(Enum):
    WHENEVER = 0
    NEXT = 1
    NOW = 2

class JobStatus(Enum):
    FAILED = 0
    SUCCESS = 1
    STOPPED = 2

@dataclass
class JobCallable:
    work: Callable[['Job'], JobStatus]
    callback: Callable[['Job'], None]
    creation_traceback: str

@DATA(excluded_fields=["callback", "work", "status_changed", "should_stop", "jobs", "completion_event", "running"])
@dataclass
class Job(Object):
    job_key: str = field(kw_only=True)
    # Key to identify the job type and retrieve its callables

    name: str = field(default="", kw_only=True)
    # Optional descriptive name for the job instance
    
    done: bool = field(default=False, kw_only=True)
    # Indicates whether the job has completed
    
    status: str = field(default="", kw_only=True)
    # Current status of the job
    
    status_hover: str = field(default="", kw_only=True)
    # Detailed status information for hover tooltip
    
    failed_last_run: bool = field(default=False, kw_only=True)
    # Indicates if the job failed in its last execution

    work: Callable[['Job'], JobStatus] = field(default=None, init=False)
    # The bulk of the work to be done by this job which should monitor should_stop and can return STOPPED 
    
    callback: Callable[['Job'], None] = field(default=None, init=False)
    # A quick non-blocking function to be called when work is done

    status_changed: Signal[[object, str, str], None] = Signal.field()
    # Signal emitted when the job's status changes

    jobs: 'Jobs' = field(default=None, init=False)
    # Weak reference to the Jobs instance this job belongs to

    should_stop: bool = field(default=False, init=False)
    # Flag to indicate if the job should stop execution
    
    registered: bool = field(default=True, init=False)
    # Set by Jobs class to track if this job is registered yet after loading
    
    completion_event: Event = field(default_factory=Event, init=False)
    # Event to signal job completion
    
    running: bool = field(default=False, init=False)
    # If the job is being run by any thread
    
    def start(self, priority: JobPriority = JobPriority.WHENEVER):
        """
        Start the job with the specified priority.

        :param priority: The priority level for starting the job
        """
        self.failed_last_run = False
        if self.jobs:
            self.jobs.start_job(self, priority)

    def wait(self) -> bool:
        """
        Wait until the job is done.
        :return: True if the job completed successfully, False otherwise
        """
        self.completion_event.wait()
        return self.done and not self.failed_last_run

    def __call__(self) -> JobStatus:
        """
        Execute the job's work function and handle its completion or failure.

        :return: True if the job completed successfully, False otherwise
        """
        try:
            status = JobStatus.SUCCESS
            if self.work:
                status = self.work(self)
            if self.callback:
                self.callback(self)
            if status == JobStatus.SUCCESS:
                self.done = True
            return status
        except Exception as e:
            self.status = f"Error: {str(e)}"
            job_traceback = traceback.format_exc()
            creation_traceback = self.jobs.registry[self.job_key].creation_traceback
            self.status_hover = (
                f"Error traceback:\n{job_traceback}\n\n"
                f"Job registration traceback:\n{creation_traceback}"
            )
            self.status_changed(self, self.status, self.status_hover)
            print(f"Error in job {self.name or self.job_key}: {e}")
            self.failed_last_run = True
            return JobStatus.FAILED
        finally:
            self.completion_event.set()

@DATA(included_fields=["_jobs"], excluded_fields=["changed", "thread_status_changed", "registry", "current_job"])
@dataclass
class Jobs(Object):
    _jobs: List[Job] = field(default_factory=list)
    # List of jobs to be executed

    changed: Signal[[], None] = Signal.field()
    # Signal emitted when the job list changes

    thread_status_changed: Signal[[bool], None] = Signal.field()
    # Signal emitted when the thread running status changes

    registry: ClassVar[Dict[str, JobCallable]] = {}
    # Class-level registry of job types

    _thread: Thread = field(default=None, init=False)
    # Thread for running jobs

    _stop_event: Event = field(default_factory=Event, init=False)
    # Event for signaling the thread to stop

    _lock: Lock = field(default_factory=Lock, init=False)
    # Lock for thread-safe operations on the job list

    current_job: Optional[Job] = field(default=None, init=False)
    # The job that is currently running
    
    _un_registered_jobs: List[Job] = field(default_factory=list)
    # temp list of jobs that were loaded by the orm that might not have had their callable's registered yet
    
    should_save_job: ClassVar[Signal[[Job],None]] = Signal[[Job],None]()
    # Called after the job is run so it can be saved to a db, along with it's data
    
    @staticmethod
    def singleton() -> 'Jobs':
        try:
            return Jobs._singleton
        except:
            return Jobs()
        
    def __post_init__(self):
        self._un_registered_jobs = list(self._jobs)
        with self._lock:
            self._ensure_loaded_jobs_registered()
        Jobs._singleton = self
        
    def _ensure_loaded_jobs_registered(self):
        if len(self._un_registered_jobs)==0:
            return
        
        new_un_registered_jobs = []
        for job in self._un_registered_jobs:
            job.jobs = self
            
            if job.job_key in self.registry:
                job_callable = self.registry[job.job_key]
                job.work, job.callback = job_callable.work, job_callable.callback
                job.registered = True
            else:
                new_un_registered_jobs.append(job)
        self._un_registered_jobs = new_un_registered_jobs

    @property
    def jobs(self) -> List[Job]:
        """
        Get a shallow copy of the jobs list.

        :return: A copy of the jobs list
        """
        with self._lock:
            # The GIL ensures that the list copy is atomic,
            # but we use a lock for future-proofing against potential GIL removal
            return self._jobs.copy()

    @staticmethod
    def register(job_key: str, work: Callable[['Job'], JobStatus], callback: Callable[['Job'], None]):
        """
        Register a new job type with its work and callback functions.

        :param job_key: The key to identify the job type
        :param work: The bulk of the work do be done by the job, this 
        function should monitor job.should_stop and return STOPPED
        :param callback: Called after the job is finished, this should be
        quick and non-blocking.
        """
        creation_traceback = traceback.format_stack()
        Jobs.registry[job_key] = JobCallable(work, callback, ''.join(creation_traceback))

    def add(self, job: Job) -> Job:
        """
        Add a job to the jobs list and set its callables.

        :param job: The job to add
        :return: The added job
        """
        with self._lock:
            if job.job_key not in self.registry:
                raise ValueError(f"No registered job type with key: {job.job_key}")
            job_callable = self.registry[job.job_key]
            job.work, job.callback = job_callable.work, job_callable.callback
            job.jobs = self
            self._jobs.append(job)
        
        current_wait_for = WaitFor.get_current()
        if current_wait_for:
            current_wait_for.add_job(job)
        
        self.changed()
        return job

    def start_job(self, job: Job, priority: JobPriority):
        """
        Start a job with the specified priority.

        :param job: The job to start
        :param priority: The priority level for starting the job
        """
        with self._lock:
            if priority != JobPriority.WHENEVER and job in self._jobs:
                self._jobs.remove(job)

            if priority == JobPriority.NOW:
                self.stop()
                self._jobs.insert(0, job)
            elif priority == JobPriority.NEXT:
                self._jobs.insert(0 if not self._thread else 1, job)
            elif job not in self._jobs:
                self._jobs.append(job)

        self.start()
        self.changed()
    
    def execute_job(self, job:Job):
        '''
        Execute Job on current thread or wait for it
        if it's already running.
        
        This makes sure it's saved with the job list
        to file, but not dispatch it needlessly to a separate thread.
        '''
        already_running = False
        with self._lock:
            if job.running:
                already_running = True
            job.running = True
        if already_running:
            job.wait()
        else:
            self._execute_job(job)
            
    def start(self):
        """
        Start the job processing thread if it's not already running.
        """
        with self._lock:
            if self.current_job:
                self.current_job.should_stop = False
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = Thread(target=self._run)
            self._thread.start()
        self.thread_status_changed(True)

    def stop(self):
        """
        Stop the job processing thread if it's running.
        """
        thread_to_stop = None
        with self._lock:
            if self._thread and self._thread.is_alive():
                self._stop_event.set()
                if self.current_job:
                    self.current_job.should_stop = True
                thread_to_stop = self._thread
                self._thread = None
        
        if thread_to_stop:
            thread_to_stop.join()
        self.thread_status_changed(False)

    def _run(self):
        """
        The main job processing loop.
        """
        while not self._stop_event.is_set():
            with self._lock:
                for j in self._jobs:
                    if not j.registered:
                        continue
                    
                    if not j.failed_last_run and not j.running:
                        self.current_job = j
                        break

            if self.current_job:
                self._execute_job(self.current_job)
                self.current_job = None
            else:
                time.sleep(0.05)

        self.thread_status_changed(False)
    
    def _execute_job(self, job:Job):
        print(f"Starting job: {job.name or job.job_key}")
        try:
            status = job()
            changed = False
            with self._lock:
                if status == JobStatus.SUCCESS or status == None:
                    print(f"Job completed successfully: {job.name or job.job_key}")
                    self._jobs.remove(job)
                    changed = True
                elif status == JobStatus.FAILED:
                    print(f"Job failed: {job.name or job.job_key}")
                elif status == JobStatus.STOPPED:
                    print(f"Job stopped: {job.name or job.job_key}")
                job.should_stop = False
                job.running = False
            if changed:
                self.changed()
        except Exception as e:
            print(f"Error in job {job.name or job.job_key}: {e}.")
        Jobs.should_save_job(job)

class WaitFor:
    _local = threading.local()

    def __init__(self):
        self.jobs = []

    def __enter__(self):
        if not hasattr(self._local, 'WaitFor_stack'):
            self._local.WaitFor_stack = []
        self._local.WaitFor_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._local.WaitFor_stack.pop()
        Jobs().start()
        for job in self.jobs:
            job.wait()

    @classmethod
    def get_current(cls):
        if hasattr(cls._local, 'WaitFor_stack') and cls._local.WaitFor_stack:
            return cls._local.WaitFor_stack[-1]
        return None

    def add_job(self, job):
        self.jobs.append(job)

    def get_jobs(self):
        return self.jobs.copy()