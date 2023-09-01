from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy import create_engine
from .Schema import *

from typing import Iterable, Callable, Dict

class Database(ConversationCollection):
	def __init__(self, db_url:str):
		self.engine = create_engine(db_url)
		Base.metadata.create_all(self.engine)
		self.session_maker = sessionmaker(bind=self.engine)
		
		self.any:Dict[str, Callable] = {}
	
	#TODO: handle none checks
	
	def _shallow_merge(self, obj:object):
		self._session.merge( to_table_object(obj) )
		
	def _add_conversation(self, conversation:Conversation):
		self._session.add( ConversationTable.from_hashable(conversation) )
	
	def _add_message(self, message:Message):
		#TODO: ensure sure weak reference to conversation is saved?
		
		self._shallow_merge(message.source)
		self._session.add( MessageTable.from_hashable(message) )
	
	def _add_message_sequence(self, message_sequence:MessageSequence):
		#TODO: check message sequence not already added.
		#if it is, we don't want to create mappings again
		
		self._session.add( MessageSequenceTable.from_hashable(message_sequence) )
		
		for message in Message.expand_previous_messages(message_sequence.messages):
			self._add_message(message)
			
			m = MessageSequenceMappingTable()
			m.message_sequence_hash = message_sequence.hash
			m.message_hash = message.hash
			self._session.add(m)
	
	def add_conversation(self, conversation:Conversation):
		self._session = self.session_maker()
		self._add_conversation(conversation)
		self._add_message_sequence(conversation.message_sequence)
		self._session.commit()
	
	def add_message(self, message:Message):
		self._session = self.session_maker()
		for m in Message.expand_previous_messages([message]):
			self._add_message(m)
		self._session.commit()
	
	def add_message_sequence(self, message_sequence:MessageSequence):
		self._session = self.session_maker()
		self._add_message_sequence(message_sequence)
		self._session.commit()
	
	def get_any(self, hash:str) -> Hashable:
		#TODO: make sure we keep track of things that are added or got to
		#update get any's dict. We want 'get_message', 'get_conversation',
		#etc for each hash so we don't have to query each table to figure
		#out which type this is
		
		getter = self.any.get(hash, None)
		if getter is None:
			#TODO: try all tables for key here
			raise KeyError(f"hash {hash} not found.")
		return getter(hash)
		
	def get_message(self, hash:str) -> Message:
		self._session = self.session_maker()
		return MessageTable.from_hashable( self._session.query(MessageTable).filter(MessageTable.hash == hash).one() )