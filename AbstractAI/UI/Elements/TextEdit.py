from PyQt5.QtWidgets import QTextEdit
from AbstractAI.UI.Context import Context
from PyQt5.QtCore import QTimer

class TextEdit(QTextEdit):
    def __init__(self, name:str, *args, auto_save:bool=False, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.name = name
        self.auto_save = auto_save
        self.textChanged.connect(self.onTextChanged)
        if self.auto_save:
            QTimer.singleShot(0, self.load_settings)

    def insertFromMimeData(self, source):
        if source.hasText():
            # Strip any formatting from the text and insert it as plain text
            plain_text = source.text()
            self.insertPlainText(plain_text)
    
    def load_settings(self):
        if self.auto_save:
            self.setPlainText(Context.settings.value(f"{self.name}/text", ""))
            self.textChanged.emit()
            
    def onTextChanged(self):
        if self.auto_save:
            Context.settings.setValue(f"{self.name}/text", self.toPlainText())