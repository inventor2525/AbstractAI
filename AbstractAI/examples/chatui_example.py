from AbstractAI.UI.ChatViews.MessageView_extras import *
from AbstractAI.UI.ChatViews.ConversationView import *

import json
from AbstractAI.Helpers.JSONEncoder import JSONEncoder
from ClassyFlaskDB.DATA import DATAEngine
data_engine = DATAEngine(ConversationDATA)

#create a QT window with a message view in it:
app = QApplication(sys.argv)

conv = Conversation("Test Conversation", "A test conversation")
conv.add_message( Message("You are a helpful assistant", UserSource("System")) )
conv.add_message( Message("Say hello", UserSource()) )
conv.add_message( Message("Hello!", ModelSource(ModelInfo("LLM","A model"))) )

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

horizontal_layout = QHBoxLayout()
#button to display the messages in the conversation:
button = QPushButton("Print Conversation")
button.clicked.connect(lambda: print_conversation(conv))
horizontal_layout.addWidget(button)

#button to add a message to the conversation:
button = QPushButton("Add Message")
button.clicked.connect(lambda: conv.add_message(Message("Hello WORLD!!", UserSource())))
horizontal_layout.addWidget(button)

layout.addLayout(horizontal_layout)

#show the window:
window.show()

#run the QT event loop:
sys.exit(app.exec_())