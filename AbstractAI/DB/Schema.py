from sqlalchemy import  Column, Integer, String, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from typing import Type, Iterable, Tuple

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

def attributes_of(obj):
	return [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("_")]

def get_all_hashable_attributes(table_obj:"HashableTable", hashable_obj:Hashable) -> Iterable[Tuple[str, str]]:
	'''returns attr, attr_hash pairs'''
	table_obj_attributes = set(attributes_of(table_obj))
	hashable_obj_attributes = attributes_of(hashable_obj)
	
	return [(attr, f"{attr}_hash") for attr in hashable_obj_attributes if f"{attr}_hash" in table_obj_attributes]
	
def transfer_fields_properties(source:object, target:object):
	source_attributes = attributes_of(source)
	target_attributes = attributes_of(target)

	for attr in source_attributes:
		if attr in target_attributes:
			try:
				setattr(target, attr, getattr(source, attr))
			except:
				pass
	return source_attributes, target_attributes
			
def to_hashable(cc:ConversationCollection, schema_obj:"HashableTable", hashable_class:Type[Hashable]) -> Hashable:
	hashable_obj = hashable_class()
	s_as, h_as = transfer_fields_properties(schema_obj, hashable_obj)
	
	for hash_attr in h_as: #TODO: consolidate this with get_all_hashable_attributes
		schema_attr = f"{hash_attr}_hash"
		if schema_attr in s_as:
			hash_val = getattr(schema_obj, schema_attr, None)
			setattr(hashable_obj, hash_attr, cc.get_any(hash_val))
	return hashable_obj

def from_hashable(hashable_obj:Hashable, schema_class:Type["HashableTable"]) -> "HashableTable":
	schema_obj = schema_class()
	h_as, s_as = transfer_fields_properties(hashable_obj, schema_obj)
	
	for hash_attr in h_as: #TODO: consolidate this with get_all_hashable_attributes
		schema_attr = f"{hash_attr}_hash"
		if schema_attr in s_as:
			inner_hashable = getattr(hashable_obj, hash_attr, None)
			inner_hash = None
			if inner_hashable is not None:
				inner_hash = inner_hashable.hash
			setattr(schema_obj, schema_attr, inner_hash)
	return schema_obj

def get_table_class_by_table_name(table_name:str) -> Type[Base]:
	return {
		m.class_.__tablename__:m.class_
		for m in Base.registry.mappers
		if not m.class_.__name__.startswith('_')
	}[table_name]

def get_attributes_foreignkey_table_class(table_class:Type[Base], attr_name:str) -> Type[Base]:
	attr_foreign_key = next(iter(getattr(table_class, attr_name).foreign_keys),None)
	attrs_target_table_name = attr_foreign_key.column.table.name
	return get_table_class_by_table_name( attrs_target_table_name )

class HashableTable(Base):
	__abstract__ = True
	__target_class__ = object
	
	def to_hashable(self, cc: ConversationCollection) -> Hashable:
		return to_hashable(cc, self, self.get_target_class())

	@classmethod
	def from_hashable(cls, hashable_obj: Hashable) -> "HashableTable":
		return from_hashable(hashable_obj, cls)
	
	def get_target_class(self) -> Type[Hashable]:
		return self.__target_class__
	
	@staticmethod
	def get_table_class(hashable_obj:Type[Hashable]) -> Type["HashableTable"]:
		return globals()[f"{hashable_obj.__name__}Table"]
		
class ConversationTable(HashableTable):
	__tablename__ = 'Conversations'
	__target_class__ = Conversation
	
	hash = Column(String, primary_key=True)
	creation_time = Column(DateTime)
	name = Column(String)
	description = Column(String)
	message_sequence_hash = Column(String, ForeignKey('MessageSequences.hash'))

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

def get_table_class_by_hashable_name(hashable_name:str) -> Type[Base]:
	# return {
	# 	m.class_.__name__:m.class_
	# 	for m in Base.registry.mappers
	# 	if not m.class_.__name__.startswith('_')
	# }[hashable_name]   ????
	return globals()[f"{hashable_name}Table"]
	
def to_table_object(obj) -> HashableTable:
	'''Auto locates the table object for the passed object and calls from_hashable on it.'''
	table_type = get_table_class_by_hashable_name(obj.__class__.__name__)
	return table_type.from_hashable(obj)