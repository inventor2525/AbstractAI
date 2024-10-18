from dataclasses import dataclass, field
from enum import Enum
from typing import List, Callable, Dict, Tuple, Optional, ClassVar, Type
import time
import traceback
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

@DATA(excluded_fields=["callback", "work", "status_changed", "should_stop", "jobs"])
@dataclass
class Job(Object):
    job_key: str
    # Key to identify the job type and retrieve its callables

    name: str = ""
    # Optional descriptive name for the job instance
    
    done: bool = False
    # Indicates whether the job has completed
    
    status: str = ""
    # Current status of the job
    
    status_hover: str = ""
    # Detailed status information for hover tooltip
    
    failed_last_run: bool = False
    # Indicates if the job failed in its last execution

    work: Callable[['Job'], JobStatus] = field(init=False)
    # The bulk of the work to be done by this job which should monitor should_stop and can return STOPPED 
    
    callback: Callable[['Job'], None] = field(init=False)
    # A quick non-blocking function to be called when work is done

    status_changed: Signal[[object, str, str], None] = Signal.field()
    # Signal emitted when the job's status changes

    jobs: 'Jobs' = field(init=False, default=None)
    # Weak reference to the Jobs instance this job belongs to

    should_stop: bool = field(default=False, init=False)
    # Flag to indicate if the job should stop execution

    def start(self, priority: JobPriority = JobPriority.WHENEVER):
        """
        Start the job with the specified priority.

        :param priority: The priority level for starting the job
        """
        self.failed_last_run = False
        if self.jobs:
            self.jobs.start_job(self, priority)

    def wait(self):
        """
        Wait until the job is done.
        """
        while not self.done:
            time.sleep(0.05)

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
    
    def __post_init__(self):
        self._un_registered_jobs = list(self._jobs)
        with self._lock:
            self._ensure_loaded_jobs_registered()
        
    def _ensure_loaded_jobs_registered(self):
        new_urj = []
        for job in self._un_registered_jobs:
            job.jobs = self
            
            if job.job_key in self.registry:
                job_callable = self.registry[job.job_key]
                job.work, job.callback = job_callable.work, job_callable.callback
            else:
                new_urj.append(job)
        self._un_registered_jobs = new_urj

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
        print("Job processing thread started")
        while not self._stop_event.is_set():
            with self._lock:
                for j in self._jobs:
                    if not j.failed_last_run and (j.work or j.callback):
                        self.current_job = j
                        break
                else:
                    self.current_job = None

            if self.current_job:
                print(f"Starting job: {self.current_job.name or self.current_job.job_key}")
                try:
                    status = self.current_job()
                    changed = False
                    with self._lock:
                        if status == JobStatus.SUCCESS or status == None:
                            print(f"Job completed successfully: {self.current_job.name or self.current_job.job_key}")
                            self._jobs.remove(self.current_job)
                            changed = True
                        elif status == JobStatus.FAILED:
                            print(f"Job failed: {self.current_job.name or self.current_job.job_key}")
                        elif status == JobStatus.STOPPED:
                            print(f"Job stopped: {self.current_job.name or self.current_job.job_key}")
                        self.current_job.should_stop = False
                    if changed:
                        self.changed()
                except Exception as e:
                    print(f"Error in job {self.current_job.name or self.current_job.job_key}: {e}. Moving to the next job.")
                
                Jobs.should_save_job(self.current_job)
                self.current_job = None
            else:
                time.sleep(0.05)

        print("Job processing thread stopped")
        self.thread_status_changed(False)