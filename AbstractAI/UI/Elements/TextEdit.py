from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QTextEdit
from AbstractAI.AppContext import AppContext
from AbstractAI.UI.QtContext import QtContext
from PyQt5.QtCore import QTimer

class TextEdit(QTextEdit):
    def __init__(self, name:str, *args, auto_save:bool=False, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.name = name
        self.auto_save = auto_save
        self.textChanged.connect(self.onTextChanged)
        if self.auto_save:
            QTimer.singleShot(0, self.load_settings)
        
        self._height_known = False

    def insertFromMimeData(self, source):
        if source.hasText():
            # Strip any formatting from the text and insert it as plain text
            plain_text = source.text()
            self.insertPlainText(plain_text)
    
    def load_settings(self):
        if self.auto_save:
            self._height_known = False
            self.setPlainText(QtContext.settings.value(f"{self.name}/text", ""))
            self.textChanged.emit()
            
    def onTextChanged(self):
        if self.auto_save:
            QtContext.settings.setValue(f"{self.name}/text", self.toPlainText())
        self._height_known = False
    
    def clearSelection(self):
        c = self.textCursor()
        c.setPosition(c.position())
        self.setTextCursor(c)
    
    def doc_height(self, max_chars:int=10000, max_height:int=10000) -> int:
        '''
        Returns the height of the document in pixels clamped to max_height
        but only if the number of characters is less than max_chars.
        
        If the number of characters is greater than max_chars then max_height
        is returned.
        
        This is useful for determining the height of the document when the
        document's length is too long to calculate in a reasonable amount of
        time.
        '''
        #TODO: calculate the height of the document when the number of characters
        # is greater than max_chars rather than just returning max_height
        
        if not self._height_known or self._doc_height < max_height:
            chars = len(self.toPlainText())
            if chars < max_chars:
                self._doc_height = int(self.document().size().height())
                if self._doc_height > max_height:
                    self._doc_height = max_height
            else:
                self._doc_height = max_height
            self._height_known = True
        
        return self._doc_height