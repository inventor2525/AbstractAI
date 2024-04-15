import os
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeView,
                             QFileDialog, QLabel, QLineEdit, QApplication, QSpacerItem,
                             QSizePolicy)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt5.QtCore import Qt, QEvent, pyqtSignal
from AbstractAI.ConversationModel.MessageSources.FilesSource import ItemModel, FolderModel

class FileFolderTreeView(QTreeView):
    onSelectionChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super(FileFolderTreeView, self).__init__(parent)
        self.model = QStandardItemModel()
        self.setModel(self.model)
        self.model.setHorizontalHeaderLabels(['Name'])
        self.setSelectionMode(QTreeView.ExtendedSelection)

    def addItems(self, paths, isFolder=False, model=None):
        for path in paths:
            item = QStandardItem(os.path.basename(path))
            item.setToolTip(path)
            if isFolder:
                item.setFont(QFont("Arial", weight=QFont.Bold))
            item.setData(model, Qt.UserRole)
            self.model.appendRow(item)
    
    def selectionChanged(self, selected, deselected):
        super(FileFolderTreeView, self).selectionChanged(selected, deselected)
        self.onSelectionChanged.emit()

class FileFilterWidget(QWidget):
    def __init__(self, parent=None):
        super(FileFilterWidget, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.pattern_label = QLabel("File Pattern:")
        self.pattern_line_edit = QLineEdit()
        self.folder_pattern_label = QLabel("Folder Pattern:")
        self.folder_pattern_line_edit = QLineEdit()
        self.extension_label = QLabel("File Extensions:")
        self.extension_line_edit = QLineEdit()
        self.refresh_button = QPushButton("Refresh")
        
        self.layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.layout.addWidget(self.pattern_label)
        self.layout.addWidget(self.pattern_line_edit)
        self.layout.addWidget(self.folder_pattern_label)
        self.layout.addWidget(self.folder_pattern_line_edit)
        self.layout.addWidget(self.extension_label)
        self.layout.addWidget(self.extension_line_edit)
        self.layout.addWidget(self.refresh_button)
        self.setLayout(self.layout)

class FileSelectionWidget(QWidget):
    def __init__(self, parent=None):
        super(FileSelectionWidget, self).__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.tree_view_and_buttons_widget = QWidget()
        self.tree_view_layout = QVBoxLayout()
        self.tree_view_layout.setContentsMargins(0, 0, 0, 0)
        self.tree_view_and_buttons_widget.setLayout(self.tree_view_layout)
        self.layout.addWidget(self.tree_view_and_buttons_widget, 2)
        
        self.tree_view = FileFolderTreeView()
        self.tree_view_layout.addWidget(self.tree_view)

        self.buttons_layout = QHBoxLayout()
        self.add_file_button = QPushButton("Add Files")
        self.add_folder_button = QPushButton("Add Folders")
        self.buttons_layout.addWidget(self.add_file_button)
        self.buttons_layout.addWidget(self.add_folder_button)
        self.tree_view_layout.addLayout(self.buttons_layout)

        self.file_filter_widget = FileFilterWidget()
        self.layout.addWidget(self.file_filter_widget, 1)
        self.file_filter_widget.hide()
        
        self.file_filter_widget.layout.setContentsMargins(0, 0, 0, 0)
        self.file_filter_widget.setFixedWidth(200)
        
        self.add_file_button.clicked.connect(self.addFiles)
        self.add_folder_button.clicked.connect(self.addFolders)
        self.file_filter_widget.pattern_line_edit.textEdited.connect(self.updateFolderPattern)
        self.file_filter_widget.folder_pattern_line_edit.textEdited.connect(self.updateFolderPattern)
        self.file_filter_widget.extension_line_edit.textEdited.connect(self.updateFolderPattern)
        
        self.tree_view.onSelectionChanged.connect(self.itemSelected)
        self.file_filter_widget.refresh_button.clicked.connect(self.refreshFolder)
        self._items = []
        
        self.tree_view_and_buttons_widget.setFixedHeight(self.file_filter_widget.sizeHint().height())
        self.tree_view.installEventFilter(self)
        self.setFixedHeight(self.file_filter_widget.sizeHint().height())

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and event.key() == Qt.Key_Delete
                and source is self.tree_view):
            # Delete Selected Items:
            selected_indexes = self.tree_view.selectedIndexes()
            for index in sorted(selected_indexes, key=lambda index: index.row(), reverse=True):
                item = index.data(Qt.UserRole)
                if item is not None:
                    self._items = [i for i in self._items if i is not item]
                    self.tree_view.model.removeRow(index.row())
            return True
        return super(FileSelectionWidget, self).eventFilter(source, event)

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        self._items = items
        self.tree_view.model.clear()
        self.tree_view.model.setHorizontalHeaderLabels(['Name'])
        for item in self._items:
            if isinstance(item, FolderModel):
                self.tree_view.addItems([item.path], isFolder=True, model=item)
            else:
                self.tree_view.addItems([item.path], model=item)

    def addFiles(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*)")
        for file in files:
            item = ItemModel(path=file)
            self._items.append(item)
            self.tree_view.addItems([file], model=item)

    def addFolders(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            folder_model = FolderModel(path=folder)
            self._items.append(folder_model)
            self.tree_view.addItems([folder], isFolder=True, model=folder_model)
    
    def updateFolderPattern(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            selected_item = self.tree_view.model.itemFromIndex(selected_indexes[0])
            folder_model = selected_item.data(Qt.UserRole)
            if folder_model:
                folder_model.file_pattern = self.file_filter_widget.pattern_line_edit.text()
                folder_model.folder_pattern = self.file_filter_widget.folder_pattern_line_edit.text()
                folder_model.extension_pattern = self.file_filter_widget.extension_line_edit.text()
                
    def itemSelected(self):
        if len(self.tree_view.selectedIndexes()) != 1:
            self.file_filter_widget.hide()
            return
        
        index = self.tree_view.selectedIndexes()[0]
        item = index.data(Qt.UserRole)
        if item is None:
            self.file_filter_widget.hide()
            return
        
        if type(item) == FolderModel:
            self.file_filter_widget.show()
            self.file_filter_widget.pattern_line_edit.setText(item.file_pattern)
            self.file_filter_widget.folder_pattern_line_edit.setText(item.folder_pattern)
            self.file_filter_widget.extension_line_edit.setText(item.extension_pattern)
        else:
            self.file_filter_widget.hide()

    def refreshFolder(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            selected_item = self.tree_view.model.itemFromIndex(selected_indexes[0])
            folder_model = selected_item.data(Qt.UserRole)
            if folder_model and os.path.isdir(folder_model.path):
                selected_item.removeRows(0, selected_item.rowCount())
                folder_model.file_pattern = self.file_filter_widget.pattern_line_edit.text()
                folder_model.folder_pattern = self.file_filter_widget.folder_pattern_line_edit.text()
                found = self.exploreFolder(folder_model.path, selected_item, folder_model.file_pattern, folder_model.folder_pattern, folder_model.allowed_extensions)
                if not found:
                    parent = selected_item.parent()
                    if parent:
                        parent.removeRow(selected_item.row())

    def exploreFolder(self, folder_path, parent_item, file_pattern, folder_pattern, allowed_extensions):
        found = False
        for entry in os.listdir(folder_path):
            full_path = os.path.join(folder_path, entry)
            if os.path.isdir(full_path) and re.match(folder_pattern, entry):
                folder_item = QStandardItem(entry)
                folder_item.setToolTip(full_path)
                folder_item.setFont(QFont("Arial", italic=True))
                folder_item.setForeground(Qt.darkBlue)
                if self.exploreFolder(full_path, folder_item, file_pattern, folder_pattern, allowed_extensions):
                    parent_item.appendRow(folder_item)
                    found = True
            elif os.path.isfile(full_path) and re.match(file_pattern, entry):
                extension = os.path.splitext(full_path)[1][1:]
                if allowed_extensions and extension not in allowed_extensions:
                    continue
                file_item = QStandardItem(entry)
                file_item.setToolTip(full_path)
                file_item.setFont(QFont("Arial", italic=True))
                file_item.setForeground(Qt.darkBlue)
                parent_item.appendRow(file_item)
                found = True
        return found
    
    def clear(self):
        self.tree_view.model.clear()
        self._items.clear()
        self.tree_view.model.setHorizontalHeaderLabels(['Name'])

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    widget = QWidget()
    layout = QVBoxLayout(widget)
    file_selector = FileSelectionWidget()
    layout.addWidget(file_selector)
    
    def printItems():
        for item in file_selector.items:
            print(item.path)
            if isinstance(item, FolderModel):
                print(f"file_pattern: '{item.file_pattern}'")
                print(f"folder_pattern: '{item.folder_pattern}'")
                print(f"extension_pattern: '{item.extension_pattern}'")
            print()
    
    button = QPushButton("Print Items")
    button.clicked.connect(printItems)
    layout.addWidget(button)
    
    def print_items_matching_patterns():
        for path in ItemModel.iterate_files(file_selector.items):
            print(path)
    button2 = QPushButton("Print Items Matching Patterns")
    button2.clicked.connect(print_items_matching_patterns)
    layout.addWidget(button2)
    widget.show()
    sys.exit(app.exec_())