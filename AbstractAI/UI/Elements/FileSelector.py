import os
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeView,
                             QFileDialog, QLabel, QLineEdit, QStandardItemModel, QStandardItem)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class FileFolderTreeView(QTreeView):
    def __init__(self, parent=None):
        super(FileFolderTreeView, self).__init__(parent)
        self.model = QStandardItemModel()
        self.setModel(self.model)
        self.model.setHorizontalHeaderLabels(['Name'])

    def addItems(self, paths, isFolder=False):
        for path in paths:
            item = QStandardItem(os.path.basename(path))
            item.setToolTip(path)
            if isFolder:
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

class FileSelectionWidget(QWidget):
    def __init__(self, parent=None):
        super(FileSelectionWidget, self).__init__(parent)
        self.layout = QHBoxLayout(self)

        self.tree_view_layout = QVBoxLayout()
        self.tree_view = FileFolderTreeView()
        self.tree_view_layout.addWidget(self.tree_view)

        self.buttons_layout = QHBoxLayout()
        self.add_file_button = QPushButton("Add Files")
        self.add_folder_button = QPushButton("Add Folders")
        self.buttons_layout.addWidget(self.add_file_button)
        self.buttons_layout.addWidget(self.add_folder_button)
        self.tree_view_layout.addLayout(self.buttons_layout)

        self.layout.addLayout(self.tree_view_layout, 2)

        self.file_filter_widget = FileFilterWidget()
        self.layout.addWidget(self.file_filter_widget, 1)
        self.file_filter_widget.hide()

        self.add_file_button.clicked.connect(self.addFiles)
        self.add_folder_button.clicked.connect(self.addFolders)
        self.tree_view.clicked.connect(self.itemSelected)
        self.file_filter_widget.refresh_button.clicked.connect(self.refreshFolder)

    def addFiles(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*)")
        self.tree_view.addItems(files)

    def addFolders(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:  # Check if a folder was selected
            self.tree_view.addItems([folder], isFolder=True)

    def itemSelected(self, index):
        item = self.tree_view.model.itemFromIndex(index)
        if item.font().weight() == QFont.Bold:  # Check if the item is a folder
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
                selected_item.removeRows(0, selected_item.rowCount())  # Clear existing items
                for entry in os.listdir(folder_path):
                    full_path = os.path.join(folder_path, entry)
                    if os.path.isfile(full_path) and re.match(pattern, entry):
                        child_item = QStandardItem(entry)
                        selected_item.appendRow(child_item)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    widget = FileSelectionWidget()
    widget.show()
    sys.exit(app.exec_())