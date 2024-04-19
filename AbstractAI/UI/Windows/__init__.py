import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QStackedLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout, QLabel, QLineEdit, QComboBox, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class SettingsWindow(QWidget):
    settingsSaved = pyqtSignal()

    def __init__(self, models, paths):
        super().__init__()
        self.models = models
        self.paths = paths
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Settings")
        self.setGeometry(300, 300, 800, 600)

        # Main layout
        mainLayout = QHBoxLayout()

        # Tree view setup
        self.treeView = QTreeView()
        self.treeModel = QStandardItemModel()
        self.treeView.setModel(self.treeModel)
        mainLayout.addWidget(self.treeView, 1)  # Add tree view to main layout

        # Placeholder for settings area
        self.settingsArea = QWidget()
        mainLayout.addWidget(self.settingsArea, 2)  # Placeholder widget for settings

        # Save button setup
        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.saveSettings)
        buttonLayout = QVBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.saveButton)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)  # Set the main layout to the window

        self.buildTreeModel()

    def buildTreeModel(self):
        for i, (model, path) in enumerate(zip(self.models, self.paths)):
            parent = self.treeModel.invisibleRootItem()
            for part in path.split("/"):
                parent = self.findOrAddChild(parent, part)
            item = QStandardItem(model.__name__)
            parent.appendRow([item])
            item.model = model
            item.path = path

    def findOrAddChild(self, parent, name):
        for row in range(parent.rowCount()):
            if parent.child(row).text() == name:
                return parent.child(row)
        item = QStandardItem(name)
        parent.appendRow([item])
        return item
    

    def saveSettings(self):
        self.settingsSaved.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Example model classes
    class Model1:
        a: int
        b: str
        c: bool

    class Model2:
        d: list
        e: int

    models = [Model1, Model2]
    paths = ["Path/To/Model1", "Path/To/Model2"]

    window = SettingsWindow(models, paths)
    window.show()

    sys.exit(app.exec_())