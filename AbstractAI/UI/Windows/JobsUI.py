from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, QHeaderView, QStyledItemDelegate, QApplication
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor
from AbstractAI.UI.Support._CommonImports import *
from AbstractAI.UI.Context import Context
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread
from AbstractAI.Helpers.Jobs import Job, Jobs, JobPriority
from ClassyFlaskDB.new.ClassInfo import ClassInfo

class JobsTableModel(QAbstractTableModel):
    def __init__(self, jobs: Jobs):
        super().__init__()
        self.jobs = jobs
        self.jobs.changed.connect(self.update)
        self.columns = ["Status", "Start"]
        self.update()

    def update(self):
        """
        Update the model data and structure.
        """
        self.beginResetModel()
        job_fields = set()
        for job in self.jobs.jobs:
            if not hasattr(job, 'view'):
                job_fields.update(field.name for field in ClassInfo.get(job.__class__).fields.values()
                                  if field.name not in ["callback", "work", "status_changed", "_jobs", "auto_id", "done", "failed_last_run", "source", "tags", "status", "status_hover"])
        
        prioritized_fields = ["name", "date_created", "callback_name"]
        remaining_fields = sorted(job_fields - set(prioritized_fields))
        self.columns.extend(prioritized_fields + remaining_fields)
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
    def __init__(self, jobs:Jobs):
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