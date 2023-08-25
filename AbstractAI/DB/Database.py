from AbstractAI.Conversation import *

class Database:
	def __init__(self, db_url:str):
		self.engine = create_engine(db_url)
		Base.metadata.create_all(self.engine)
		self.Session = sessionmaker(bind=self.engine)
	
	def _add_message(self, message:Message):
		session = self.Session()
		message.source.recompute_hash()
		message.recompute_hash()
		
		#TODO: Convert types:
		session.add(message.source)
		session.add(message)
		session.commit()
		
	def add_message(self, message:Message):
		messages_to_add = [message]
		closed_list = set(messages_to_add)
		
		prev_message = message.prev_message
		while prev_message is not None:
			if prev_message in closed_list:
				break
			messages_to_add.append(message)
			closed_list.add(message)
			
			prev_message = prev_message.prev_message
		
		for m in reversed(messages_to_add):
			self._add_message(m)

	def add_conversation(self, conversation:Conversation):
		session = self.Session()
		for message in conversation.messages:
			self.add_message(message)
		conversation.recompute_hash()
		
		session.add(conversation)
		session.commit()
