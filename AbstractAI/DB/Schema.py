from sqlalchemy import  Column, Integer, String, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from typing import Type

from .ConversationCollection import *

Base = declarative_base()
def get_all_subclasses(cls):
	all_subclasses = []
	to_check = [cls]
	
	while to_check:
		current_class = to_check.pop()
		current_subclasses = current_class.__subclasses__()
		
		all_subclasses.extend(current_subclasses)
		to_check.extend(current_subclasses)
		
	return all_subclasses
		
def transfer_fields_properties(source:object, target:object):
	source_attributes = [attr for attr in dir(source) if not callable(getattr(source, attr)) and not attr.startswith("_")]
	target_attributes = [attr for attr in dir(target) if not callable(getattr(target, attr)) and not attr.startswith("_")]

	for attr in source_attributes:
		if attr in target_attributes:
			setattr(target, attr, getattr(source, attr))
	return source_attributes, target_attributes
			
def to_hashable(cc:ConversationCollection, schema_obj:"HashableTable", hashable_class:Type[Hashable]) -> Hashable:
	hashable_obj = hashable_class()
	s_as, h_as = transfer_fields_properties(schema_obj, hashable_obj)
	
	for hash_attr in h_as:
		schema_attr = f"{hash_attr}_hash"
		if schema_attr in s_as:
			hash_val = getattr(schema_obj, schema_attr, None)
			setattr(hashable_obj, hash_attr, cc.get_any(hash_val))
	return hashable_obj

def from_hashable(hashable_obj:Hashable, schema_class:Type["HashableTable"]) -> "HashableTable":
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
	
class HashableTable(Base):
	__abstract__ = True
	__target_class__ = object
	
	def to_hashable(self, cc: ConversationCollection) -> Hashable:
		return to_hashable(cc, self, self.__target_class__)

	@classmethod
	def from_hashable(cls, hashable_obj: Hashable) -> "HashableTable":
		return from_hashable(hashable_obj, cls)
		
class ConversationTable(HashableTable):
	__tablename__ = 'Conversations'
	__target_class__ = Conversation
	
	hash = Column(String, primary_key=True)
	creation_time = Column(DateTime)
	name = Column(String)
	description = Column(String)
	message_sequence_hash = Column(String)

class MessageSequenceTable(HashableTable):
	__tablename__ = 'MessageSequences'
	__target_class__ = MessageSequence
	
	hash = Column(String, primary_key=True)
	conversation_hash = Column(String, ForeignKey('Conversations.hash'))

	def to_hashable(self, cc:ConversationCollection) -> MessageSequence:
		ms = super().to_hashable(cc)
		#TODO: load from MessageSequenceMappingTable the message hashes of this sequence, then load the messages
		return ms

	@classmethod
	def from_hashable(cls, hashable_obj:MessageSequence) -> "MessageSequenceTable":
		ms = super().from_hashable(hashable_obj)
		#TODO: save the message hashes for this message sequence in MessageSequenceMappingTable
		return ms
		
class MessageSequenceMappingTable(Base):
	__tablename__ = '_MessageSequenceMapping'
	id = Column(Integer, primary_key=True)
	message_sequence_hash = Column(String, ForeignKey('MessageSequences.hash'))
	message_hash = Column(String, ForeignKey('Messages.hash'))
	
class MessageTable(HashableTable):
	__tablename__ = 'Messages'
	__target_class__ = Message
	
	hash = Column(String, primary_key=True)
	creation_time = Column(DateTime)
	content = Column(String)
	role = Column(Enum(Role))
	
	_source_type = Column(String)
	_source_hash = Column(String)
	
	prev_message_hash = Column(String, ForeignKey('Messages.hash'))
	conversation_hash = Column(String, ForeignKey('Conversations.hash'))
	
	@property
	def source(self):
		#Query the database for source_hash at the table named based on source_type:
		# source_type = globals()[f"{self.source_type}Table"]
		# return static_session.query(source_type).filter(source_type.hash == self.source_hash).first()		
		return None
	@source.setter
	def source(self, value):
		self._source_type = value.__class__.__name__
		self._source_hash = value.hash
	
class BaseMessageSourceTable(HashableTable):
	__abstract__ = True
	hash = Column(String, primary_key=True)

class EditSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_Edit'
	__target_class__ = EditSource
	
	original_hash = Column(String, ForeignKey('Messages.hash'))
	new_hash = Column(String, ForeignKey('Messages.hash'))

class ModelSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_Model'
	__target_class__ = ModelSource
	
	class_name = Column(String)
	model_name = Column(String)
	other_parameters = Column(JSON)
	message_sequence_hash = Column(String, ForeignKey('MessageSequences.hash'))
	models_serialized_raw_output = Column(String)
	
class TerminalSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_Terminal'
	__target_class__ = TerminalSource
	
	command = Column(String)
		
class UserSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_User'
	__target_class__ = UserSource
	
	user_name = Column(String)
	
def to_table_object(obj) -> HashableTable:
	'''Auto locates the table object for the passed object and calls from_hashable on it.'''
	table_type = globals()[f"{obj.__class__.__name__}Table"]
	return table_type.from_hashable(obj)