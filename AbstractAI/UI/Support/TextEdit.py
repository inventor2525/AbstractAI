from PyQt5.QtWidgets import QTextEdit

class TextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.setAcceptRichText(False)

    def insertFromMimeData(self, source):
        if source.hasText():
            # Strip any formatting from the text and insert it as plain text
            plain_text = source.text()
            self.insertPlainText(plain_text)