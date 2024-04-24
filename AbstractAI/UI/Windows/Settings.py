import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QStackedLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout, QLabel, QLineEdit, QComboBox, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from dataclasses import dataclass

from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar, Dict, Generic, List, Tuple, Callable
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
		return None
	
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
	def __init__(self, model, path, view_factory=None, view_factories=None):
		self.model = model
		self.path = path
		self.view_factory = view_factory
		self.view_factories:List[Tuple[str,Callable[[],QWidget]]] = view_factories
		
class TreeViewItem(QStandardItem):
	def __init__(self, *args, **kwargs):
		super(TreeViewItem, self).__init__(*args, **kwargs)
		self.isAlwaysExpanded = False
		
class TreeView(QTreeView):
	def __init__(self, *args, **kwargs):
		super(TreeView, self).__init__(*args, **kwargs)
		self.collapsed.connect(self.preventCollapse)
		
	def drawBranches(self, painter, rect, index):
		'''
		Override the drawBranches method to prevent disclosure 
		triangles from being drawn on items that are always expanded.
		'''
		item = self.model().itemFromIndex(index)
		if hasattr(item, 'isAlwaysExpanded') and item.isAlwaysExpanded:
			pass
		else:
			super(TreeView, self).drawBranches(painter, rect, index)
	
	def preventCollapse(self, index):
		item = self.model().itemFromIndex(index)
		if getattr(item, 'isAlwaysExpanded', False):
			self.expand(index)
			
class SettingsWindow(QWidget):
	settingsSaved = pyqtSignal()

	def __init__(self, setting_items):
		super().__init__()
		self.setting_items = setting_items
		self.initUI()
		self.redrawItems()

	def initUI(self):
		self.setWindowTitle("Settings")
		self.setGeometry(300, 300, 800, 600)

		mainLayout = QHBoxLayout()

		self.treeView = TreeView()
		self.treeView.setHeaderHidden(True)
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

		self.treeView.selectionModel().selectionChanged.connect(self._displayModel)
	
	def _clearItems(self):
		while self.treeModel.rowCount():
			self.treeModel.removeRow(0)
		self.all_items = []
		
	def _add_item(self, setting_item: SettingItem) -> None:
		parent = self.treeModel.invisibleRootItem()
		indent_level = 0
		for part in setting_item.path.split("/"):
			parent = self.findOrAddChild(parent, part)
			parent.indent_level = indent_level
			self.all_items.append(parent)
			indent_level += 1
		item = parent
		item.setting_item = setting_item
		item.setting_model = setting_item.model
		item.isTopLevelItem = True
		self._addChildren(item, setting_item.model)
	
	def _refresh_item_font(self, item: QStandardItem) -> None:
		if getattr(item, 'setting_model', None) is not None:
			if getattr(item, 'isTopLevelItem', False):
				item.setForeground(Qt.blue)
			else:
				item.setForeground(Qt.darkBlue)
		else:
			item.isAlwaysExpanded = True
			item.setSelectable(False)
			index = self.treeModel.indexFromItem(item)
			self.treeView.expand(index)
			
			indent_level = getattr(item, 'indent_level', -1)
			
			if indent_level == 0:
				font = item.font()
				font.setPointSize(20)
				font.setBold(True)
				item.setFont(font)
			elif indent_level == 1:
				font = item.font()
				font.setPointSize(15)
				font.setBold(True)
				item.setFont(font)
			elif indent_level == 2:
				font = item.font()
				font.setItalic(True)
				font.setBold(True)
				item.setFont(font)
				
	def redrawItems(self):
		self._clearItems()
		for setting_item in self.setting_items:
			self._add_item(setting_item)
		
		for item in self.all_items:
			self._refresh_item_font(item)
	
	def addSettingItem(self, setting_item: SettingItem) -> None:
		self.setting_items.append(setting_item)
		old_all_items = self.all_items
		self.all_items = []
		self._add_item(setting_item)
		for item in self.all_items:
			self._refresh_item_font(item)
		self.all_items = old_all_items + self.all_items
		
	def _addChildren(self, parent, model_instance):
		if hasattr(model_instance, '__annotations__'):
			for field_name, field_type in model_instance.__annotations__.items():
				field_value = getattr(model_instance, field_name)
				if TypedControls.get_control(field_type) is not None:
					continue
				elif hasattr(field_value, '__annotations__'):
					item = self.findOrAddChild(parent, field_name)
					self.all_items.append(item)
					self._addChildren(item, field_value)
					item.setting_model = field_value
				else:
					pass
				
	def findOrAddChild(self, parent, name):
		for row in range(parent.rowCount()):
			if parent.child(row).text() == name:
				return parent.child(row)
		item = QStandardItem(name)
		parent.appendRow([item])
		return item

	def _displayModel(self):
		def clear_forum_layout():
			while self.formLayout.count():
				child = self.formLayout.takeAt(0)
				if child.widget():
					child.widget().deleteLater()
		clear_forum_layout()
		
		selection = self.treeView.selectionModel().selectedIndexes()
		if len(selection) == 0:
			return
		
		index = selection[0]
		item = self.treeModel.itemFromIndex(index)
		setting_item = getattr(item, 'setting_item', None)
		setting_model = getattr(item, 'setting_model', None)
		
		if setting_item is not None and setting_item.view_factory is not None:
			self.formLayout.addRow(setting_item.view_factory())
		elif setting_model is not None and hasattr(setting_model, "__annotations__"):
			for field_name, field_type in setting_model.__annotations__.items():
				field_value = getattr(setting_model, field_name)
				control_type = TypedControls.get_control(field_type)
				if control_type is None:
					continue
				control = control_type(field_type)
				control.value = field_value
				def change_value(control=control, model=setting_model, field_name=field_name):
					setattr(model, field_name, control.value)
				control.valueChanged.connect(change_value)
				self.formLayout.addRow(QLabel(field_name), control)
				
			if setting_item is not None:
				if setting_item.view_factories is not None:
					for view_factory in setting_item.view_factories:
						self.formLayout.addRow(QLabel(view_factory[0]), view_factory[1]())
		else:
			clear_forum_layout()
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
	
	@dataclass
	class NestedChild:
		name:str
		model1: Model1
		
	@dataclass
	class NestedModel:
		name:str
		description:str
		child: NestedChild
		model2: Model2
	
	#Demo starting a settings window with some items:
	model1 = Model1(42, "hello world", True)
	model2 = Model2([1,2,3], 42, myEnum.two)
	model3 = Model2([1,2,3], 42, myEnum.two)
	nested_model = NestedModel(
		"linked test", "This is tied to the 2 models above, changing this will change those",
		NestedChild("child 1", model1), model2
	)
	nested_model_2 = NestedModel(
		"unlinked test", "This is not tied to the 2 models above, changing this will not change anything else",
		NestedChild("child 2", Model1(1, "Hi", False)),
		Model2([4,5,6], 1, myEnum.three)
	)
	setting_items = [
		SettingItem(model1, "Items/Model1"),
		SettingItem(model2, "Items/Model2"),
		SettingItem(model3, "Items/Model2/Model3"),
		SettingItem(nested_model, "Items/Nested/Linked Model"),
		SettingItem(nested_model_2, "Items/Nested/UnLinked Model"),
	]
	window = SettingsWindow(setting_items)
	window.show()
	
	#Demo adding more items after the fact with a 
	#control in the auto generated setting view:
	num = 0
	def add_more_models_demo():
		global num
		@dataclass
		class bla:
			a: int
			b: str
			c: bool
			d: list
			e: int
		@dataclass
		class Dummy:
			int_field: int
			float_field: float
			str_field: str
			bool_field: bool
			list_field: list
			nest: bla
		
		dummy = Dummy(0, 0.0, "", False, [], bla(0, "", False, [], 0))
		window.addSettingItem(SettingItem(dummy, f"Things/More Things/Even More Things/Stuff/Things/Dummy{num}"))
		num += 1
	def add_more_button_maker():
		b = QPushButton("Add More")
		b.clicked.connect(add_more_models_demo)
		return b
	
	window.addSettingItem(SettingItem(
		Model1(1, "hi", True),
		"Add More Demo", 
		view_factories=[("Add More Models", add_more_button_maker)]
		)
	)
	
	#Demo adding a totally custom view to settings:
	def custom_view_factory() -> QWidget:
		custom_view = QWidget()
		layout = QVBoxLayout()
		label = QLabel("Custom View")
		layout.addWidget(label)
		layout.addWidget(QLabel("It's custom, totally custom!!!"))
		layout.addSpacing(200)
		layout.addWidget(QLabel("Isn't it cool?"))
		h_layout = QHBoxLayout()
		h_layout.addWidget(QLabel("Hello"))
		h_layout.addWidget(QLineEdit())
		h_layout.addWidget(QLabel("World"))
		h_layout.addWidget(QComboBox())
		layout.addLayout(h_layout)
		layout.addSpacing(100)
		layout.addWidget(QLabel("SO COOL!"))
		custom_view.setLayout(layout)
		return custom_view
	
	window.addSettingItem(SettingItem(
		Model1(0, "", False), 
		"Custom View", view_factory=custom_view_factory
		)
	)

	sys.exit(app.exec_())