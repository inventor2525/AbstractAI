import os
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTreeView, QFileDialog, QLabel,
                             QLineEdit)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt5.QtCore import Qt

class FileFolderTreeView(QTreeView):
    def __init__(self, parent=None):
        super(FileFolderTreeView, self).__init__(parent)
        self.model = QStandardItemModel()
        self.setModel(self.model)
        self.model.setHorizontalHeaderLabels(['Name'])

    def addItems(self, paths):
        for path in paths:
            item = QStandardItem(os.path.basename(path))
            item.setToolTip(path)
            if os.path.isdir(path):
                item.setFont(QFont("Arial", weight=QFont.Bold))
            self.model.appendRow(item)

class FileFilterWidget(QWidget):
    def __init__(self, parent=None):
        super(FileFilterWidget, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.pattern_label = QLabel("Regex Pattern:")
        self.pattern_line_edit = QLineEdit()
        self.refresh_button = QPushButton("Refresh")
        self.layout.addWidget(self.pattern_label)
        self.layout.addWidget(self.pattern_line_edit)
        self.layout.addWidget(self.refresh_button)
        self.setLayout(self.layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("File and Folder Selection")
        self.resize(800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        self.tree_view = FileFolderTreeView()
        self.layout.addWidget(self.tree_view, 2)

        self.file_filter_widget = FileFilterWidget()
        self.layout.addWidget(self.file_filter_widget, 1)
        self.file_filter_widget.hide()

        self.add_button = QPushButton("Add Files/Folders")
        self.add_button.clicked.connect(self.addItems)

        self.tree_view.clicked.connect(self.itemSelected)

        self.file_filter_widget.refresh_button.clicked.connect(self.refreshFolder)

        self.bottom_layout = QVBoxLayout()
        self.bottom_layout.addWidget(self.add_button)
        self.layout.addLayout(self.bottom_layout)

    def addItems(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Files and Folders", "", "All Files (*)", options=QFileDialog.DontUseNativeDialog)
        self.tree_view.addItems(paths)

    def itemSelected(self, index):
        item = self.tree_view.model.itemFromIndex(index)
        if os.path.isdir(item.toolTip()):
            self.file_filter_widget.show()
        else:
            self.file_filter_widget.hide()

    def refreshFolder(self):
        pattern = self.file_filter_widget.pattern_line_edit.text()
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            selected_item = self.tree_view.model.itemFromIndex(selected_indexes[0])
            folder_path = selected_item.toolTip()
            if os.path.isdir(folder_path):
                for entry in os.listdir(folder_path):
                    full_path = os.path.join(folder_path, entry)
                    if os.path.isfile(full_path) and re.match(pattern, entry):
                        child_item = QStandardItem(entry)
                        selected_item.appendRow(child_item)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())