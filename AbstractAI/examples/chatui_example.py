from AbstractAI.UI.Support.MessageView import *
from AbstractAI.UI.Support.ConversationView import *

import json
from ClassyFlaskDB.Flaskify.serialization import FlaskifyJSONEncoder
from ClassyFlaskDB.DATA import DATAEngine
data_engine = DATAEngine(DATA)

#create a QT window with a message view in it:
app = QApplication(sys.argv)

conv = Conversation("Test Conversation", "A test conversation")
conv.add_message( Message("You are a helpful assistant", UserSource("System")) )
conv.add_message( Message("Say hello", UserSource()) )
conv.add_message( Message("Hello!", ModelSource("LLM","A model")) )
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
button = QPushButton("Print Conversation")
button.clicked.connect(lambda: print_conversation(conv))
layout.addWidget(button)

#show the window:
window.show()

#run the QT event loop:
sys.exit(app.exec_())