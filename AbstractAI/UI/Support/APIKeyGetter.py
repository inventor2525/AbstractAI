import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QWidget
from PyQt5.QtCore import QSettings

def APIKeyGetter(api_name, settings, instructions=""):
    class KeyDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("API Key Required")
            self.layout = QVBoxLayout(self)

            self.instruction_label = QLabel(f"Please enter the API key for {api_name}. {instructions}")
            self.key_input = QLineEdit(self)
            self.key_input.setPlaceholderText("API Key")

            self.confirm_button = QPushButton("Confirm", self)
            self.confirm_button.clicked.connect(self.accept)

            self.cancel_button = QPushButton("Cancel", self)
            self.cancel_button.clicked.connect(self.reject)

            self.layout.addWidget(self.instruction_label)
            self.layout.addWidget(self.key_input)
            self.layout.addWidget(self.confirm_button)
            self.layout.addWidget(self.cancel_button)

        def accept(self):
            key = self.key_input.text().strip()
            if key:
                settings.setValue(f"{api_name}_APIKey", key)
                super().accept()
            else:
                QMessageBox.warning(self, "Error", "API Key cannot be empty.")

    key = settings.value(f"{api_name}_APIKey")
    if key:
        return key
    else:
        dialog = KeyDialog()
        if dialog.exec_() == QDialog.Accepted:
            return settings.value(f"{api_name}_APIKey")
        else:
            return None