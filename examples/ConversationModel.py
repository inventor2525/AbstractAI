from AbstractAI.ConversationModel import *
from ClassyFlaskDB.DATA import *

engine = DATAEngine(ConversationDATA, engine_str="sqlite:///ConversationModel.db")


c = Conversation("Example Conversation", "A conversation to show the ConversationModel.")

m = Message.HardCoded("Hello, World!", system_message=True)
c.add_message(m)
engine.merge(m)


m = Message("Hello, World!", source=UserSource(user_name="User1"))
c.add_message(m)

m = m.create_edited("Hello, ***World***!", source_of_edit=UserSource(user_name="User2"))
c.add_message(m)
engine.merge(c)