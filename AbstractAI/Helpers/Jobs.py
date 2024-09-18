from dataclasses import dataclass, field
from enum import Enum
from typing import List, Callable, Dict, Tuple, Optional, ClassVar
from weakref import ref
import time
import traceback
from threading import Thread, Lock, Event, Condition
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, QHeaderView, QStyledItemDelegate
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor
from ClassyFlaskDB.DefaultModel import *
from AbstractAI.Helpers.Signal import Signal
from AbstractAI.UI.Support._CommonImports import *
from AbstractAI.UI.Context import Context
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread

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

    _condition: Condition = field(init=False)
    # Condition variable for thread synchronization

    def __post_init__(self):
        self._condition = Condition(self._lock)
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
                with self._condition:
                    self._condition.notify()
        if self._thread:
            self._thread.join()
        self._thread = None
        self.thread_status_changed(False)

    def _run(self):
        """
        The main job processing loop.
        """
        while not self._stop_event.is_set():
            job = None
            with self._lock:
                for i, j in enumerate(self._jobs):
                    if not j.failed_last_run:
                        job = self._jobs.pop(i)
                        break

            if job:
                success = job()
                with self._lock:
                    if success:
                        self.changed()
                    else:
                        self._jobs.append(job)
            else:
                with self._condition:
                    self._condition.wait(0.05)

        self.thread_status_changed(False)

class JobsTableModel(QAbstractTableModel):
    def __init__(self, jobs: Jobs):
        super().__init__()
        self.jobs = jobs
        self.jobs.changed.connect(self.update)
        self.columns = ["Status", "Start"]

    def update(self):
        """
        Update the model data and structure.
        """
        self.beginResetModel()
        job_fields = set()
        for job in self.jobs.jobs:
            if not hasattr(job, 'view'):
                job_fields.update(job.__class__.__class_info__.fields.keys())
        self.columns.extend(sorted(job_fields))
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self.jobs.jobs)

    def columnCount(self, parent=None):
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        job = self.jobs.jobs[index.row()]
        column = self.columns[index.column()]
        
        if column == "Status":
            if role == Qt.DisplayRole:
                return job.status
            elif role == Qt.ToolTipRole:
                return job.status_hover
        elif column == "Start":
            return None  # This column will be handled by the delegate
        elif hasattr(job, 'view'):
            return None  # This will be handled by the delegate
        elif role == Qt.DisplayRole:
            return str(getattr(job, column, "N/A"))
        elif role == Qt.BackgroundRole:
            if not hasattr(job, column):
                return QColor(0, 0, 0)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns[section]
        return None

class JobItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_buttons = {}

    def createEditor(self, parent, option, index):
        if index.column() == 1:  # Start column
            button = QPushButton("Start", parent)
            job = index.model().jobs.jobs[index.row()]
            button.clicked.connect(lambda: job.start(JobPriority.NEXT))
            self.start_buttons[index.row()] = button
            return button
        elif hasattr(index.model().jobs.jobs[index.row()], 'view'):
            return index.model().jobs.jobs[index.row()].view
        return None

    def setEditorData(self, editor, index):
        pass

    def setModelData(self, editor, model, index):
        pass

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class JobsWindow(QWidget):
    def __init__(self, jobs: Jobs):
        super().__init__()
        self.jobs = jobs
        self.init_ui()

    def init_ui(self):
        """
        Initialize the user interface.
        """
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.table_view = QTableView()
        self.model = JobsTableModel(self.jobs)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(JobItemDelegate())
        layout.addWidget(self.table_view)

        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.jobs.stop)
        layout.addWidget(self.stop_button)

        self.jobs.changed.connect(self.update_ui)
        self.jobs.thread_status_changed.connect(self.update_thread_status)

        self.update_ui()

    @run_in_main_thread
    def update_ui(self):
        """
        Update the UI elements based on the current state of jobs.
        """
        self.model.update()
        for i, job in enumerate(self.jobs.jobs):
            if i in self.table_view.itemDelegate().start_buttons:
                self.table_view.itemDelegate().start_buttons[i].setEnabled(not job.failed_last_run)
            job.status_changed.connect(self.update_job_status)

    @run_in_main_thread
    def update_thread_status(self, is_running: bool):
        """
        Update the UI based on the thread running status.

        :param is_running: Whether the job processing thread is running
        """
        self.stop_button.setEnabled(is_running)
        for button in self.table_view.itemDelegate().start_buttons.values():
            button.setEnabled(not is_running)

    @run_in_main_thread
    def update_job_status(self, job, status, hover):
        """
        Update the status of a specific job in the UI.

        :param job: The job whose status has changed
        :param status: The new status text
        :param hover: The new hover text
        """
        for i, j in enumerate(self.jobs.jobs):
            if j == job:
                self.model.dataChanged.emit(
                    self.model.index(i, 0),
                    self.model.index(i, 0)
                )
                break

# Usage example:
if __name__ == "__main__":
    app = QApplication([])
    
    jobs = Jobs()
    
    def example_work(job):
        for i in range(5):
            job.status = f"Working... {i+1}/5"
            job.status_hover = f"Detailed progress for step {i+1}"
            job.status_changed(job, job.status, job.status_hover)
            time.sleep(1)
        print(f"Doing work for {job.name}")
    
    def example_callback(job):
        job.status = "Finished"
        job.status_hover = "Job completed successfully"
        job.status_changed(job, job.status, job.status_hover)
        print(f"Finished {job.name}")
    
    Jobs.register("Example Job", example_work, example_callback)
    jobs.create("Example Job")
    
    window = JobsWindow(jobs)
    window.show()
    
    app.exec_()