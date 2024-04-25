import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QScrollArea, QLabel
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QFrame, QAbstractItemView
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QFrame, QMessageBox,  QCheckBox, QVBoxLayout, QHBoxLayout, QCompleter, QLabel, QComboBox, QTextEdit, QSizePolicy, QToolButton
from PyQt5.QtCore import Qt, QSize, QPoint, QSettings, QByteArray, pyqtSignal, QRect, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QImage, QTextOption, QColor, QPalette, QPainter
from typing import Dict, List, Tuple, Optional, Union, Callable, Any

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)