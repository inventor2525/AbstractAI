from dataclasses import dataclass, field
from PyQt5.QtCore import QSettings

@dataclass
class QtContextModel:
	settings: QSettings = None

QtContext = QtContextModel()