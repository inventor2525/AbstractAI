import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QStackedLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout, QLabel, QLineEdit, QComboBox, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from dataclasses import dataclass

from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar, Dict, Generic, List

T = TypeVar('T')

class TypedControl(Generic[T]):
	valueChanged = pyqtSignal()
	
	@property
	def value(self) -> T:
		return self._get_value()

	@value.setter
	def value(self, value: T) -> None:
		self._set_value(value)
		self.valueChanged.emit()
	
	@abstractmethod
	def _get_value(self) -> T:
		pass
	
	@abstractmethod
	def _set_value(self, value: T) -> None:
		pass

class TypedControls:
	_registry: Dict[Type, Type[TypedControl]] = {}

	@classmethod
	def register(cls, type_: Type, control_type: Type[TypedControl]) -> None:
		cls._registry[type_] = control_type

	@classmethod
	def get_control(cls, type_: Type) -> Type[TypedControl]:
		return cls._registry.get(type_)
	
	def __call__(self, type):
		def decorator(control_type):
			self.register(type, control_type)
			return control_type
		return decorator

TypedControls = TypedControls()

@TypedControls(int)
class IntControl(QLineEdit, TypedControl[int]):
	def __init__(self):
		super().__init__()
		self.textChanged.connect(self.valueChanged.emit)

	def _get_value(self) -> int:
		return int(self.text())
	
	def _set_value(self, value: int) -> None:
		self.setText(str(value))

@TypedControls(bool)
class BoolControl(QCheckBox, TypedControl[bool]):
	def __init__(self):
		super().__init__()
		self.stateChanged.connect(self.valueChanged.emit)

	def _get_value(self) -> bool:
		return self.isChecked()
	
	def _set_value(self, value: bool) -> None:
		self.setChecked(value)
		
@TypedControls(str)
class StrControl(QLineEdit, TypedControl[str]):
	def __init__(self):
		super().__init__()
		self.textChanged.connect(self.valueChanged.emit)
		
	def _get_value(self) -> str:
		return self.text()
	
	def _set_value(self, value: str) -> None:
		self.setText(value)

@TypedControls(list)
class StrListControl(QLineEdit, TypedControl[List[str]]):
	def __init__(self):
		super().__init__()
		self.textChanged.connect(self.valueChanged.emit)

	def _get_value(self) -> List[str]:
		return self.text().split(",")
	
	def _set_value(self, value: List[str]) -> None:
		self.setText(",".join([str(item) for item in value]))

class SettingItem:
	def __init__(self, model, path, view=None):
		self.model = model
		self.path = path
		self.view = view

class SettingsWindow(QWidget):
	settingsSaved = pyqtSignal()

	def __init__(self, setting_items):
		super().__init__()
		self.setting_items = setting_items
		self.initUI()

	def initUI(self):
		self.setWindowTitle("Settings")
		self.setGeometry(300, 300, 800, 600)

		mainLayout = QHBoxLayout()

		self.treeView = QTreeView()
		self.treeModel = QStandardItemModel()
		self.treeView.setModel(self.treeModel)
		mainLayout.addWidget(self.treeView, 1)

		self.formLayout = QFormLayout()
		self.formWidget = QWidget()
		self.formWidget.setLayout(self.formLayout)
		mainLayout.addWidget(self.formWidget, 2)

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
		for setting_item in self.setting_items:
			parent = self.treeModel.invisibleRootItem()
			for part in setting_item.path.split("/"):
				parent = self.findOrAddChild(parent, part)
			item = parent
			item.model = setting_item.model
			item.path = setting_item.path

	def findOrAddChild(self, parent, name):
		for row in range(parent.rowCount()):
			if parent.child(row).text() == name:
				return parent.child(row)
		item = QStandardItem(name)
		parent.appendRow([item])
		return item

	def displayModel(self):
		while self.formLayout.count():
			child = self.formLayout.takeAt(0)
			if child.widget():
				child.widget().deleteLater()
		index = self.treeView.selectionModel().selectedIndexes()[0]
		item = self.treeModel.itemFromIndex(index)
		model = item.model
		if model is not None and hasattr(model, "__annotations__"):
			for field_name, field_type in model.__annotations__.items():
				field_value = getattr(model, field_name)
				control_type = TypedControls.get_control(field_type)
				if control_type is None:
					raise ValueError(f"Unsupported type {field_type.__name__} for field {field_name}")
				control = control_type()
				control.value = field_value
				def change_value(control=control, model=model, field_name=field_name):
					setattr(model, field_name, control.value)
				control.valueChanged.connect(change_value)
				self.formLayout.addRow(QLabel(field_name), control)
		else:
			while self.formLayout.count():
				child = self.formLayout.takeAt(0)
				if child.widget():
					child.widget().deleteLater()
			self.formLayout.addRow(QLabel(""))

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

	model1 = Model1(42, "hello world", True)
	model2 = Model2([1,2,3], 42)

	setting_items = [SettingItem(model1, "Items/Model1"), SettingItem(model2, "Items/Model2")]

	window = SettingsWindow(setting_items)
	window.show()

	sys.exit(app.exec_())