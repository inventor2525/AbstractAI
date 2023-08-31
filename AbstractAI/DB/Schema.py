from AbstractAI.Conversation import *
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from typing import Type

Base = declarative_base()
class HashableTable(Base):
	__abstract__ = True

	def to_hashable(self, cc: ConversationCollection) -> Hashable:
		return to_hashable(self, self.__class__)

	@classmethod
	def from_hashable(cls, hashable_obj: Hashable) -> "HashableTable":
		return from_hashable(hashable_obj, cls)
		
def transfer_fields_properties(source:object, target:object):
	source_attributes = [attr for attr in dir(source) if not callable(getattr(source, attr)) and not attr.startswith("_")]
	target_attributes = [attr for attr in dir(target) if not callable(getattr(target, attr)) and not attr.startswith("_")]

	for attr in source_attributes:
		if attr in target_attributes:
			setattr(target, attr, getattr(source, attr))
	return source_attributes, target_attributes
			
def to_hashable(cc:ConversationCollection, schema_obj:HashableTable, hashable_class:Type[HashableTable]) -> Hashable:
	hashable_obj = hashable_class()
	s_as, h_as = transfer_fields_properties(schema_obj, hashable_obj)
	
	for hash_attr in h_as:
		schema_attr = f"{hash_attr}_hash"
		if schema_attr in s_as:
			hash_val = getattr(schema_obj, schema_attr, None)
			setattr(hashable_obj, hash_attr, cc.get_any(hash_val))
	return hashable_obj

def from_hashable(hashable_obj:Hashable, schema_class:type) -> HashableTable:
	schema_obj = schema_class()
	h_as, s_as = transfer_fields_properties(hashable_obj, schema_obj)
	
	for hash_attr in h_as:
		schema_attr = f"{hash_attr}_hash"
		if schema_attr in s_as:
			inner_hashable = getattr(hashable_obj, hash_attr, None)
			inner_hash = None
			if inner_hashable is not None:
				inner_hash = inner_hashable.hash
			setattr(schema_obj, schema_attr, inner_hash)
	return schema_obj

class ConversationCollection():
	def get_conversation(self, hash:str) -> Conversation:
		pass
	def get_message(self, hash:str) -> Message:
		pass
	def get_message_sequence(self, hash:str) -> MessageSequence:
		pass
	def get_any(self, hash:str) -> Hashable:
		pass
	
class ConversationTable(Base):
	__tablename__ = 'Conversations'
	hash = Column(String, primary_key=True)
	creation_time = Column(DateTime)
	name = Column(String)
	description = Column(String)
	message_sequence_hash = Column(String)

		
class MessageSequenceTable(HashableTable):
	__tablename__ = 'MessageSequences'
	hash = Column(String, primary_key=True)
	conversation_hash = Column(String, ForeignKey('Conversations.hash'))

	def to_hashable(self, cc:ConversationCollection) -> MessageSequence:
		ms = super().to_hashable(cc)
		#TODO: load from MessageSequenceMappingTable the message hashes of this sequence, then load the messages
		return ms

	@classmethod
	def from_hashable(cls, hashable_obj:MessageSequence) -> MessageSequenceTable:
		ms = super().from_hashable(hashable_obj)
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
	
class BaseMessageSourceTable(Base):
	__abstract__ = True
	hash = Column(String, primary_key=True)

class EditSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_Edit'
	original_hash = Column(String, ForeignKey('Messages.hash'))
	new_hash = Column(String, ForeignKey('Messages.hash'))

class ModelSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_Model'
	class_name = Column(String)
	model_name = Column(String)
	other_parameters = Column(JSON)
	message_sequence_hash = Column(String, ForeignKey('MessageSequences.hash'))
	models_serialized_raw_output = Column(String)
	
class TerminalSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_Terminal'
	command = Column(String)
		
class UserSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_User'
	user_name = Column(String)