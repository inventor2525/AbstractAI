from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy import create_engine, exists
from .Schema import *

from typing import Iterable, Dict, Tuple

class Database(ConversationCollection):
	def __init__(self, db_url:str):
		self.engine = create_engine(db_url)
		Base.metadata.create_all(self.engine)
		self.session_maker = sessionmaker(bind=self.engine)
		
		self.any:Dict[str, Hashable] = {}
	
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
			return self.any[hash]
			
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
	
	def _shallow_get(self, hash:str, table_class:Type[HashableTable]) -> Tuple[HashableTable, Hashable]:
		if hash is None:
			return None, None
		
		if hash in self.any:
			return self.any[hash]
			
		obj = self._session.query(table_class).filter(table_class.hash == hash).one()
		return obj, obj.to_hashable(self)
	
	def _get_message(self, hash:str) -> Message:
		msg_table, msg = self._shallow_get(hash, MessageTable)
		self.any[hash] = msg
		
		#Query the database for source_hash at the table named based on source_type:
		source_type = HashableTable.get_table_class(globals()[msg_table._source_type])
		source_table, source = self._shallow_get(msg_table._source_hash, source_type)	
		self.any[msg_table._source_hash] = source
		msg.source = source
		
		conversation_table, conversation = self._shallow_get(msg_table.conversation_hash, ConversationTable)
		self.any[conversation.hash] = conversation
		msg.conversation = conversation
		
		return msg
		
	def get_message(self, hash:str) -> Message:
		self._session = self.session_maker()
		self.any.clear()
		
		msg = self._get_message(hash)
		
		self._session.close()
		return msg
	