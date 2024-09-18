from dataclasses import dataclass, field
from enum import Enum
from typing import List, Callable, Dict, Tuple, Optional, ClassVar
from weakref import ref
import time
import traceback
from threading import Thread, Lock, Event, Condition
from ClassyFlaskDB.DefaultModel import *
from AbstractAI.Helpers.Signal import Signal

class JobPriority(Enum):
    WHENEVER = 0
    NEXT = 1
    NOW = 2

@dataclass
class JobCallable:
    work: Callable
    callback: Callable
    creation_traceback: str

@DATA(excluded_fields=["callback", "work", "status_changed"])
@dataclass
class Job(Object):
    name: str
    # Name of the job
    
    callback_name: str
    # Name of the callback associated with this job
    
    done: bool = False
    # Indicates whether the job has completed
    
    status: str = ""
    # Current status of the job
    
    status_hover: str = ""
    # Detailed status information for hover tooltip
    
    failed_last_run: bool = False
    # Indicates if the job failed in its last execution

    callback: Callable = field(init=False)
    # Callback function to be called when the job is done

    work: Callable = field(init=False)
    # The main work function of the job

    status_changed: Signal[[object, str, str], None] = Signal.field()
    # Signal emitted when the job's status changes

    _jobs: Optional['Jobs'] = field(init=False, default=None)
    # Weak reference to the Jobs instance this job belongs to

    def start(self, priority: JobPriority = JobPriority.WHENEVER):
        """
        Start the job with the specified priority.

        :param priority: The priority level for starting the job
        """
        self.failed_last_run = False
        if self._jobs:
            jobs = self._jobs()
            if jobs:
                jobs.start_job(self, priority)

    def wait(self):
        """
        Wait until the job is done.
        """
        while not self.done:
            time.sleep(0.05)

    def __call__(self) -> bool:
        """
        Execute the job's work function and handle its completion or failure.

        :return: True if the job completed successfully, False otherwise
        """
        try:
            if self.work:
                self.work(self)
            if self.callback:
                self.callback(self)
            self.done = True
            return True
        except Exception as e:
            self.status = f"Error: {str(e)}"
            job_traceback = traceback.format_exc()
            creation_traceback = self._jobs().registry[self.callback_name].creation_traceback
            self.status_hover = (
                f"Error traceback:\n{job_traceback}\n\n"
                f"Job registration traceback:\n{creation_traceback}"
            )
            self.status_changed(self, self.status, self.status_hover)
            print(f"Error in job {self.name}: {e}")
            self.failed_last_run = True
            return False

@DATA(excluded_fields=["changed", "thread_status_changed"])
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

    def __post_init__(self):
        for job in self._jobs:
            if job.callback_name in self.registry:
                job_callable = self.registry[job.callback_name]
                job.work, job.callback = job_callable.work, job_callable.callback
            job._jobs = ref(self)

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
    def register(name: str, work: Callable, callback: Callable):
        """
        Register a new job type with its work and callback functions.

        :param name: The name of the job type
        :param work: The work function for the job
        :param callback: The callback function for job completion
        """
        creation_traceback = traceback.format_stack()
        Jobs.registry[name] = JobCallable(work, callback, ''.join(creation_traceback))

    def create(self, callback_name: str) -> Job:
        """
        Create a new job instance.

        :param callback_name: The name of the registered job type
        :return: A new Job instance
        :raises ValueError: If the callback_name is not registered
        """
        with self._lock:
            if callback_name not in self.registry:
                raise ValueError(f"No registered callback named {callback_name}")
            job = Job(name=callback_name, callback_name=callback_name)
            job_callable = self.registry[callback_name]
            job.work, job.callback = job_callable.work, job_callable.callback
            job._jobs = ref(self)
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
        with self._lock:
            if self._thread and self._thread.is_alive():
                self._stop_event.set()
        if self._thread:
            self._thread.join()
        self._thread = None

    def _run(self):
        """
        The main job processing loop.
        """
        while not self._stop_event.is_set():
            job:Job = None
            with self._lock:
                for job in self._jobs:
                    if not job.failed_last_run:
                        break
                    job = None

            if job:
                try:
                    success = job()
                    changed = False
                    if success:
                        with self._lock:
                            self._jobs.remove(job)
                            changed = True
                    if changed:
                        self.changed()
                except:
                    print('... TODO: AI?: say the jobs name, and that youre moving onto next job?... or something')

        self.thread_status_changed(False)