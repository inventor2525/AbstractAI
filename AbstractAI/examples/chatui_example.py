from AbstractAI.UI.Support.MessageView import *
from AbstractAI.UI.Support.ConversationView import *

#create a QT window with a message view in it:
app = QApplication(sys.argv)

conv = Conversation()
conv.add_message( Message("You are a helpful assistant", Role.System, UserSource("System")) )
conv.add_message( Message("Say hello", Role.User, UserSource()) )
conv.add_message( Message("Hello!", Role.Assistant, ModelSource("LLM","A model")) )
conv.update_message_graph()

#message_view = MessageView(message)
conversation_view = ConversationView(conv)

#create a window:
window = QWidget()
window.setWindowTitle("Message View Test")
window.resize(800, 600)

#create a layout:
layout = QVBoxLayout()
window.setLayout(layout)

#add the message view to the layout:
layout.addWidget(conversation_view)

#button to display the messages in the conversation:
def print_messages(messages):
	print("=====================================")
	for message in messages:
		print(message.content)
		print(message.source)
		print(message.creation_time)
		print(message.role)
		print()
	print("=====================================")
button = QPushButton("Print Messages")
button.clicked.connect(lambda: print_messages(conv.message_sequence.messages))
layout.addWidget(button)

#show the window:
window.show()

#run the QT event loop:
sys.exit(app.exec_())