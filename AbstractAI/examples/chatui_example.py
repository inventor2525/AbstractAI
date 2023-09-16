from AbstractAI.UI.Support.MessageView import *

#create a QT window with a message view in it:
app = QApplication(sys.argv)

message = Message("Hello, world!", Role.Assistant, UserSource("System"))
message_view = MessageView(message)


#create a window:
window = QWidget()
window.setWindowTitle("Message View Test")
window.resize(800, 600)

#create a layout:
layout = QVBoxLayout()
window.setLayout(layout)

#add the message view to the layout:
layout.addWidget(message_view)

#show the window:
window.show()

#run the QT event loop:
sys.exit(app.exec_())