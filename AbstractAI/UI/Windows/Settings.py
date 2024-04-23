import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QStackedLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout, QLabel, QLineEdit, QComboBox, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from dataclasses import dataclass

from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar, Dict, Generic, List
from enum import Enum
import re
T = TypeVar('T')

class TypedControl(Generic[T]):
	valueChanged = pyqtSignal()
	
	def __init__(self, derived_type: Type[T] = None):
		self.derived_type = derived_type if derived_type is not None else T
	
	@property
	def value(self) -> T:
		return self._get_value()

	@value.setter
	def value(self, value: T) -> None:
		old_value = self._get_value()
		self._set_value(value)
		
		if old_value != value:
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
	def get_control(self, type_: Type) -> Type[TypedControl]:
		control_type = self._registry.get(type_, None)
		if control_type is not None:
			return control_type
		
		for value_type, control_type in self._registry.items():
			if issubclass(type_, value_type):
				return control_type
		raise ValueError(f"Unsupported type {type_.__name__}")
	
	def __call__(self, type):
		def decorator(control_type):
			self.register(type, control_type)
			return control_type
		return decorator

TypedControls = TypedControls()

class NumberControl(TypedControl[T], QLineEdit):
	def __init__(self, derived_type: Type[T] = None):
		QLineEdit.__init__(self)
		TypedControl.__init__(self, derived_type=derived_type)
		self._number_value:T = 0
		self.editingFinished.connect(self._validate_and_set)
	
	@abstractmethod
	def _validate(self, text: str) -> bool:
		pass
	
	def _validate_and_set(self):
		try:
			text = self.text()
			if not self._validate(text):
				return
			self.value = self._parse_value(text)
		except Exception as e:
			pass
			
	def _get_value(self) -> T:
		return self._number_value
	
	def _set_value(self, value: T) -> None:
		self._number_value = value
		self.setText(str(value))
		
	@abstractmethod
	def _parse_value(self, text: str) -> T:
		pass

@TypedControls(int)
class IntControl(NumberControl[int]):
	def _validate(self, text: str) -> bool:
		return re.match(r"^-?\d*$", text) is not None
	
	def _parse_value(self, text: str) -> int:
		return int(text)

@TypedControls(float)
class FloatControl(NumberControl[float]):
	def _validate(self, text: str) -> bool:
		return re.match(r"^-?\d*(\.\d*)?$", text) is not None
	
	def _parse_value(self, text: str) -> float:
		return float(text)

@TypedControls(bool)
class BoolControl(QCheckBox, TypedControl[bool]):
	def __init__(self, derived_type: Type[T] = None):
		QCheckBox.__init__(self)
		TypedControl.__init__(self, derived_type=derived_type)
		self.stateChanged.connect(self.valueChanged.emit)

	def _get_value(self) -> bool:
		return self.isChecked()
	
	def _set_value(self, value: bool) -> None:
		self.setChecked(value)
		
@TypedControls(str)
class StrControl(QLineEdit, TypedControl[str]):
	def __init__(self, derived_type: Type[T] = None):
		QLineEdit.__init__(self)
		TypedControl.__init__(self, derived_type=derived_type)
		self.textChanged.connect(self.valueChanged.emit)
		
	def _get_value(self) -> str:
		return self.text()
	
	def _set_value(self, value: str) -> None:
		self.setText(value)

@TypedControls(list)
class StrListControl(QLineEdit, TypedControl[List[str]]):
	def __init__(self, derived_type: Type[T] = None):
		QLineEdit.__init__(self)
		TypedControl.__init__(self, derived_type=derived_type)
		self.textChanged.connect(self.valueChanged.emit)

	def _get_value(self) -> List[str]:
		return self.text().split(",")
	
	def _set_value(self, value: List[str]) -> None:
		self.setText(",".join([str(item) for item in value]))
		
@TypedControls(Enum)
class EnumControl(QComboBox, TypedControl[Enum]):
	def __init__(self, derived_type: Type[T] = None):
		QComboBox.__init__(self)
		TypedControl.__init__(self, derived_type=derived_type)
		self.currentTextChanged.connect(self.valueChanged.emit)

	def _get_value(self) -> Enum:
		for enum_value in self.derived_type:
			if enum_value.name == self.currentText():
				return enum_value
		return None

	def _set_value(self, value: Enum) -> None:
		if not isinstance(value, Enum):
			raise ValueError("Value must be an Enum")
		if self.currentText != value.name:
			self.repopulate(value.__class__)
			self.setCurrentText(value.name)

	def repopulate(self, enum_type: Type[Enum]):
		self.clear()
		for enum_value in enum_type:
			self.addItem(enum_value.name)
			
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
				try:
					control_type = TypedControls.get_control(field_type)
				except ValueError:
					continue
				control = control_type(field_type)
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
	
	class myEnum(Enum):
		one = 1
		two = 2
		three = 3
		
	@dataclass
	class Model1:
		a: int
		b: str
		c: bool

	@dataclass
	class Model2:
		d: list
		e: int
		f: myEnum

	model1 = Model1(42, "hello world", True)
	model2 = Model2([1,2,3], 42, myEnum.two)

	setting_items = [SettingItem(model1, "Items/Model1"), SettingItem(model2, "Items/Model2")]

	window = SettingsWindow(setting_items)
	window.show()

	sys.exit(app.exec_())