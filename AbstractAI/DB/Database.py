from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy import create_engine, exists
from .Schema import *

from typing import Iterable, Dict, Tuple

class Database(ConversationCollection):
	def __init__(self, db_url:str):
		self.engine = create_engine(db_url)
		Base.metadata.create_all(self.engine)
		self.session_maker = sessionmaker(bind=self.engine)
		
		self.any:Dict[str, Tuple[HashableTable, Hashable]] = {}
	
	#TODO: handle none checks
	
	def _hash_in_table(self, hash:str, table_class:Type[HashableTable]) -> bool:
		(has_key,) = self._session.query(exists().where(table_class.hash == hash)).one()
		return has_key
		
	def _shallow_merge(self, obj:object):
		self._session.merge( to_table_object(obj) )
		
	def _add_conversation(self, conversation:Conversation):
		self._session.add( ConversationTable.from_hashable(conversation) )
	
	def _add_message(self, message:Message):
		#TODO: ensure sure weak reference to conversation is saved?
		
		self._shallow_merge(message.source)
		self._shallow_merge(message)
	
	def _add_message_sequence(self, message_sequence:MessageSequence):
		if self._hash_in_table(message_sequence.hash, MessageSequenceTable):
			return
		
		self._session.add( MessageSequenceTable.from_hashable(message_sequence) )
		
		for message in Message.expand_previous_messages(message_sequence.messages):
			self._add_message(message)
			
			m = MessageSequenceMappingTable()
			m.message_sequence_hash = message_sequence.hash
			m.message_hash = message.hash
			self._session.add(m)
	
	def add_conversation(self, conversation:Conversation):
		self._session = self.session_maker()
		self._shallow_merge(conversation)
		self._add_message_sequence(conversation.message_sequence)
		self._session.commit()
		self._session.close()
	
	def add_message(self, message:Message):
		self._session = self.session_maker()
		for m in Message.expand_previous_messages([message]):
			self._add_message(m)
		self._session.commit()
		self._session.close()
	
	def add_message_sequence(self, message_sequence:MessageSequence):
		self._session = self.session_maker()
		self._add_message_sequence(message_sequence)
		self._session.commit()
		self._session.close()
	
	def get_any(self, hash:str) -> Hashable:
		if hash is None:
			return None
			
		if hash in self.any:
			return self.any[hash][1]
			
		if self._hash_in_table(hash, ConversationTable):
			return self.get_conversation(hash)
		elif self._hash_in_table(hash, MessageTable):
			return self.get_message(hash)
		elif self._hash_in_table(hash, MessageSequenceTable):
			return self.get_message_sequence(hash)
		else:
			for hashable_table_class in get_all_subclasses(HashableTable):
				if self._hash_in_table(hash, hashable_table_class):
					getter = lambda hash: hashable_table_class.from_hashable( self._session.query(hashable_table_class).filter(hashable_table_class.hash == hash).one() )
					break
		
		raise KeyError(f"hash {hash} not found.")
	#def shallow_load(...):
	#  get from any dict if exists
	#  load non-hashable fields
	#  set to any dict
	def _shallow_get(self, hash:str, table_class:Type[HashableTable]) -> Tuple[HashableTable, Hashable]:
		if hash is None:
			return None, None
		if hash in self.any:
			return self.any[hash]
			
		obj_table = self._session.query(table_class).filter(table_class.hash == hash).one()
		obj = obj_table.to_hashable(self)
		self.any[hash] = (obj_table, obj)
		
		return (obj_table, obj)
	
	#
	#def deep_load(hash):
	#  table_obj, obj = shallow load 
	#  to_deep_load = [(table_obj,obj)]
	#  while to_deep_load:
		#  for hashable_field in hashable_fields:
		#     deep = hashable field in any
		#     set:  shallow load hashable field
		#     if deep:
		#         deep load hashable field
	def _deep_get(self, hash:str, table_class:Type[HashableTable]) -> Tuple[HashableTable, Hashable]:
		if hash is None:
			return None, None
		if hash in self.any:
			return self.any[hash]
		
		obj_table, obj = self._shallow_get(hash, table_class)
		to_deep_load = [(obj_table, obj)]
		while len(to_deep_load) > 0:
			table_obj, obj = to_deep_load.pop()
			for inner_obj_attr, inner_table_attr in get_all_hashable_attributes(table_obj, obj):
				inner_hash = getattr(table_obj, inner_table_attr, None)
				if inner_hash is None:
					setattr(obj, inner_obj_attr, None)
					continue
				if inner_hash in self.any:
					setattr(obj, inner_obj_attr, self.any[inner_hash][1])
				else:
					#Get the Hashable derived type of inner_obj_attr using the HashableTable class's foreign key:
					#!!!!!!!!!TODO!!!!!!!!!!
					inner_table_class = HashableTable.get_table_class(getattr(obj, inner_obj_attr).__class__)
					inner_table, inner_obj = self._shallow_get(inner_hash, inner_table_class)
					setattr(obj, inner_obj_attr, inner_obj)
					to_deep_load.append((inner_table, inner_obj))
			
		return (obj_table, obj)
	#
	# idea: implement custom deep loaders for each hashable type
	def _get_message(self, hash:str) -> Message:
		msg_table, msg = self._deep_get(hash, MessageTable)
		return msg
		
	def get_message(self, hash:str) -> Message:
		self._session = self.session_maker()
		self.any.clear()
		
		msg = self._get_message(hash)
		
		self._session.close()
		return msg
	