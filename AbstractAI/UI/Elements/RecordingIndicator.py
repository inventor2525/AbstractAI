from datetime import datetime
import math
from PyQt5.QtWidgets import QWidget, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QMouseEvent

class RecordingIndicator(QWidget):
    clicked = pyqtSignal()
    def __init__(self, diameter=60):
        super().__init__()

        self.diam = diameter
        self.dot_color = QColor(255, 0, 0)  # Initial color for not recording

        # Widget attributes
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.diam, self.diam)
        self.setWindowFlags(self.windowFlags() | Qt.X11BypassWindowManagerHint)

        self.is_recording = False
        self.is_processing = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_color)
        self.timer.start(10)  # Update color every 10ms

        self._positionOnPrimaryMonitor()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(self.dot_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(-self.diam/2), int(-self.diam/2), self.diam, self.diam)

    def _positionOnPrimaryMonitor(self):
        primaryMonitor = QDesktopWidget().primaryScreen()
        screenGeometry = QDesktopWidget().screenGeometry(primaryMonitor)
        self.move(screenGeometry.topLeft())

    def _update_color(self):
        if self.is_processing:
            self.dot_color = QColor(100, 100, 255)
        elif self.is_recording:
            self.dot_color = QColor(int(math.sin(datetime.now().timestamp() * 3) * 30 + 225), 0, 0)
        else:
            self.dot_color = QColor(0, 255, 0)
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if self._is_point_in_circle(event.pos()):
            self.clicked.emit()
            super().mousePressEvent(event)  # Forward the event

    def _is_point_in_circle(self, point: QPoint):
        circle_center = QPoint(0, 0)
        distance_to_center = (point - circle_center).manhattanLength()
        return distance_to_center <= self.diam / 2

# Usage Example
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    circle_widget = RecordingIndicator()
    circle_widget.show()
    sys.exit(app.exec_())
