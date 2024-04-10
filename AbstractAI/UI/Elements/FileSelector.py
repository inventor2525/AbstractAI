import os
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeView,
                             QFileDialog, QLabel, QLineEdit, QApplication)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt5.QtCore import Qt

class FolderModel:
    def __init__(self, path, file_pattern='', folder_pattern=''):
        self.path = path
        self.file_pattern = file_pattern
        self.folder_pattern = folder_pattern
        
class FileFolderTreeView(QTreeView):
    def __init__(self, parent=None):
        super(FileFolderTreeView, self).__init__(parent)
        self.model = QStandardItemModel()
        self.setModel(self.model)
        self.model.setHorizontalHeaderLabels(['Name'])

    def addItems(self, paths, isFolder=False, folder_model=None):
        for path in paths:
            item = QStandardItem(os.path.basename(path))
            item.setToolTip(path)
            if isFolder:
                item.setFont(QFont("Arial", weight=QFont.Bold))
                item.setData(folder_model, Qt.UserRole)
            self.model.appendRow(item)

class FileFilterWidget(QWidget):
    def __init__(self, parent=None):
        super(FileFilterWidget, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.pattern_label = QLabel("Regex Pattern:")
        self.pattern_line_edit = QLineEdit()
        self.folder_pattern_label = QLabel("Folder Pattern:")  # New folder pattern label
        self.folder_pattern_line_edit = QLineEdit()  # New folder pattern line edit
        self.refresh_button = QPushButton("Refresh")
        self.layout.addWidget(self.pattern_label)
        self.layout.addWidget(self.pattern_line_edit)
        self.layout.addWidget(self.folder_pattern_label)  # Add folder pattern label to layout
        self.layout.addWidget(self.folder_pattern_line_edit)  # Add folder pattern line edit to layout
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
        
        self.file_filter_widget.layout.setContentsMargins(0, 0, 0, 0)
        self.file_filter_widget.setFixedWidth(200)
        
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
            folder_model = FolderModel(folder)
            self.tree_view.addItems([folder], isFolder=True, folder_model=folder_model)

    def itemSelected(self, index):
        item = self.tree_view.model.itemFromIndex(index)
        if item.font().weight() == QFont.Bold:  # Check if the item is a folder
            self.file_filter_widget.show()
            folder_model = item.data(Qt.UserRole)
            if folder_model:
                self.file_filter_widget.pattern_line_edit.setText(folder_model.file_pattern)
                self.file_filter_widget.folder_pattern_line_edit.setText(folder_model.folder_pattern)
        else:
            self.file_filter_widget.hide()

    def refreshFolder(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            selected_item = self.tree_view.model.itemFromIndex(selected_indexes[0])
            folder_model = selected_item.data(Qt.UserRole)
            if folder_model and os.path.isdir(folder_model.path):
                selected_item.removeRows(0, selected_item.rowCount())  # Clear existing items
                folder_model.file_pattern = self.file_filter_widget.pattern_line_edit.text()
                folder_model.folder_pattern = self.file_filter_widget.folder_pattern_line_edit.text()
                found = self.exploreFolder(folder_model.path, selected_item, folder_model.file_pattern, folder_model.folder_pattern)
                if not found:
                    parent = selected_item.parent()
                    if parent:
                        parent.removeRow(selected_item.row())

    def exploreFolder(self, folder_path, parent_item, file_pattern, folder_pattern):
        found = False
        for entry in os.listdir(folder_path):
            full_path = os.path.join(folder_path, entry)
            if os.path.isdir(full_path) and re.match(folder_pattern, entry):
                folder_item = QStandardItem(entry)
                folder_item.setToolTip(full_path)
                folder_item.setFont(QFont("Arial", italic=True))
                folder_item.setForeground(Qt.darkBlue)
                if self.exploreFolder(full_path, folder_item, file_pattern, folder_pattern):
                    parent_item.appendRow(folder_item)
                    found = True
            elif os.path.isfile(full_path) and re.match(file_pattern, entry):
                file_item = QStandardItem(entry)
                file_item.setToolTip(full_path)
                file_item.setFont(QFont("Arial", italic=True))
                file_item.setForeground(Qt.darkBlue)
                parent_item.appendRow(file_item)
                found = True
        return found

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    widget = FileSelectionWidget()
    widget.show()
    sys.exit(app.exec_())