from AbstractAI.Conversation import *
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

def transfer_fields_properties(source, target):
    source_attributes = [attr for attr in dir(source) if not callable(getattr(source, attr)) and not attr.startswith("__")]
    target_attributes = [attr for attr in dir(target) if not callable(getattr(target, attr)) and not attr.startswith("__")]
    
    for attr in source_attributes:
        if attr in target_attributes:
            setattr(target, attr, getattr(source, attr))
            
def to_hashable(schema_obj, hashable_class):
    hashable_obj = hashable_class()
    transfer_fields_properties(schema_obj, hashable_obj)
    return hashable_obj

def from_hashable(hashable_obj, schema_class):
    schema_obj = schema_class()
    transfer_fields_properties(hashable_obj, schema_obj)
    return schema_obj

class ConversationCollection():
	def get_conversation(self, hash:str) -> Conversation:
		pass
	def get_message(self, hash:str) -> Message:
		pass
	def get_message_sequence(self, hash:str) -> MessageSequence:
		pass
	
class ConversationTable(Base):
	__tablename__ = 'Conversations'
	hash = Column(String, primary_key=True)
	creation_time = Column(DateTime)
	name = Column(String)
	description = Column(String)
	message_sequence_hash = Column(String)

	def to_hashable(self, cc:ConversationCollection) -> Conversation:
		conv = to_hashable(self, Conversation)
		conv.message_sequence = cc.get_message_sequence(self.message_sequence_hash)
		return conv

	@classmethod
	def from_hashable(cls, hashable_obj:Conversation) -> ConversationTable:
		conv = from_hashable(hashable_obj, cls)
		conv.message_sequence_hash = hashable_obj.message_sequence.hash
		return conv
		
class MessageSequenceTable(Base):
	__tablename__ = 'MessageSequences'
	hash = Column(String, primary_key=True)
	conversation_hash = Column(String, ForeignKey('Conversations.hash'))

	def to_hashable(self, cc:ConversationCollection) -> MessageSequence:
		ms = to_hashable(self, MessageSequence)
		#TODO: load from MessageSequenceMappingTable the message hashes of this sequence, then load the messages
		return ms

	@classmethod
	def from_hashable(cls, hashable_obj:MessageSequence) -> MessageSequenceTable:
		ms = from_hashable(hashable_obj, cls)
		#TODO: save the message hashes for this message sequence in MessageSequenceMappingTable
		return ms
		
class MessageSequenceMappingTable(Base):
	__tablename__ = '_MessageSequenceMapping'
	id = Column(Integer, primary_key=True)
	hash = Column(String, ForeignKey('MessageSequences.hash'))
	message_hash = Column(String, ForeignKey('Messages.hash'))

	def to_hashable(self, cc:ConversationCollection):
		raise Exception("Only use to_hashable on MessageSequenceTable")

	@classmethod
	def from_hashable(cls, hashable_obj):
		raise Exception("Only use from_hashable on MessageSequenceTable")
		
class MessageTable(Base):
	__tablename__ = 'Messages'
	hash = Column(String, primary_key=True)
	creation_time = Column(DateTime)
	content = Column(String)
	role = Column(String)
	
	_source_type = Column(String)
	_source_hash = Column(String)
	
	prev_message_hash = Column(String, ForeignKey('Messages.hash'))
	conversation_hash = Column(String, ForeignKey('Conversations.hash'))

	@property
	def source(self):
		session = Session()  # Assuming Session is your SQLAlchemy session class
		if self.source_type == 'user_source':
			return session.query(UserSource).filter_by(hash=self.source_hash).first()
		elif self.source_type == 'model_source':
			return session.query(ModelSource).filter_by(hash=self.source_hash).first()
		# ... handle other source types ...

	@source.setter
	def source(self, value):
		if isinstance(value, UserSource):
			self.source_type = 'user_source'
		elif isinstance(value, ModelSource):
			self.source_type = 'model_source'
		# ... handle other source types ...
		self.source_hash = value.hash
		
	def to_hashable(self, cc:ConversationCollection) -> Message:
		msg = to_hashable(self, Message)
		msg.prev_message = cc.get_message(self.prev_message_hash)
		msg.conversation = cc.get_conversation(self.conversation_hash)
		return msg

	@classmethod
	def from_hashable(cls, hashable_obj:Message) -> MessageTable:
		ms = from_hashable(hashable_obj, cls)
		ms.prev_message_hash = hashable_obj.prev_message.hash
		ms.conversation_hash = hashable_obj.conversation.hash
		return ms
	
class BaseMessageSourceTable(Base):
	__abstract__ = True
	hash = Column(String, primary_key=True)

class EditSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_Edit'
	original_hash = Column(String, ForeignKey('Messages.hash'))
	new_hash = Column(String, ForeignKey('Messages.hash'))

	def to_hashable(self, cc:ConversationCollection) -> EditSource:
		es = to_hashable(self, EditSource)
		es.original = cc.get_message(self.original_hash)
		es.new = cc.get_message(self.new_hash)
		return es

	@classmethod
	def from_hashable(cls, hashable_obj:EditSource) -> EditSourceTable:
		es = from_hashable(hashable_obj, cls)
		es.original_hash = hashable_obj.original.hash
		es.new_hash = hashable_obj.new.hash
		return es
		
class ModelSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_Model'
	class_name = Column(String)
	model_name = Column(String)
	other_parameters = Column(JSON)
	message_sequence_hash = Column(String, ForeignKey('MessageSequences.hash'))
	models_serialized_raw_output = Column(String)
	
	def to_hashable(self, cc:ConversationCollection) -> ModelSource:
		ms = to_hashable(self, ModelSource)
		return ms

	@classmethod
	def from_hashable(cls, hashable_obj:ModelSource) -> ModelSourceTable:
		ms = from_hashable(hashable_obj, cls)
		return ms
		
class TerminalSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_Terminal'
	command = Column(String)
	
	def to_hashable(self, cc:ConversationCollection) -> TerminalSource:
		return to_hashable(self, TerminalSource)

	@classmethod
	def from_hashable(cls, hashable_obj:TerminalSource) -> TerminalSourceTable:
		return from_hashable(hashable_obj, cls)
		
class UserSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_User'
	user_name = Column(String)
	
	def to_hashable(self, cc:ConversationCollection) -> UserSource:
		return to_hashable(self, UserSource)

	@classmethod
	def from_hashable(cls, hashable_obj:UserSource) -> UserSourceTable:
		return from_hashable(hashable_obj, cls)