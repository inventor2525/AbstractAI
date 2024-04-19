import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QStackedLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout, QLabel, QLineEdit, QComboBox, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from dataclasses import dataclass

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

		mainLayout = QHBoxLayout()

		self.treeView = QTreeView()
		self.treeModel = QStandardItemModel()
		self.treeView.setModel(self.treeModel)
		mainLayout.addWidget(self.treeView, 1)

		self.settingsArea = QWidget()
		settingsLayout = QVBoxLayout()
		self.formLayout = QFormLayout()
		settingsLayout.addLayout(self.formLayout)
		self.settingsArea.setLayout(settingsLayout)
		mainLayout.addWidget(self.settingsArea, 2)

		self.saveButton = QPushButton("Save")
		self.saveButton.clicked.connect(self.saveSettings)
		buttonLayout = QVBoxLayout()
		buttonLayout.addStretch()
		buttonLayout.addWidget(self.saveButton)
		mainLayout.addLayout(buttonLayout)

		self.setLayout(mainLayout)

		self.treeView.selectionModel().selectionChanged.connect(self.displayModel)

		self.buildTreeModel()

	def buildTreeModel(self):
		for i, (model, path) in enumerate(zip(self.models, self.paths)):
			parent = self.treeModel.invisibleRootItem()
			for part in path.split("/"):
				parent = self.findOrAddChild(parent, part)
			item = parent
			item.model = model
			item.path = path

	def findOrAddChild(self, parent, name):
		for row in range(parent.rowCount()):
			if parent.child(row).text() == name:
				return parent.child(row)
		item = QStandardItem(name)
		parent.appendRow([item])
		return item

	def displayModel(self, selected, deselected):
		self.formLayout.setParent(None)
		self.formLayout = QFormLayout()
		index = self.treeView.selectionModel().selectedIndexes()[0]
		item = self.treeModel.itemFromIndex(index)
		model = item.model
		if model is not None:
			for field in vars(model).items():
				if isinstance(field[1], int):
					widget = QLineEdit()
				elif isinstance(field[1], bool):
					widget = QCheckBox()
				elif isinstance(field[1], str):
					widget = QLineEdit()
				elif isinstance(field[1], list):
					widget = QComboBox()
				else:
					raise NotImplementedError(f"Unsupported type {field[1].__class__.__name__} {field}")
				self.formLayout.addRow(QLabel(field[0]), widget)
		else:
			self.formLayout = QFormLayout()

	def saveSettings(self):
		self.settingsSaved.emit()

if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setStyle("Fusion")

	@dataclass
	class Model1:
		a: int
		b: str
		c: bool

	@dataclass
	class Model2:
		d: list
		e: int

	models = [Model1(42,"hello world", True), Model2([1,2,3], 42)]
	paths = ["Items/Model1", "Items/Model2"]

	window = SettingsWindow(models, paths)
	window.show()

	sys.exit(app.exec_())