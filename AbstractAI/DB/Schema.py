from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class ConversationTable(Base):
	__tablename__ = 'Conversations'
	hash = Column(String, primary_key=True)
	creation_time = Column(DateTime)
	name = Column(String)
	description = Column(String)
	message_sequence_hash = Column(String)

class MessageSequenceTable(Base):
	__tablename__ = 'MessageSequences'
	hash = Column(String, primary_key=True)
	conversation_hash = Column(String, ForeignKey('Conversations.hash'))

class MessageSequenceTable(Base):
	__tablename__ = 'MessageSequenceMapping'
	id = Column(Integer, primary_key=True)
	hash = Column(String, ForeignKey('MessageSequences.hash'))
	message_hash = Column(String, ForeignKey('Messages.hash'))

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
	models_raw_output = Column(JSON)
	
class TerminalSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_Terminal'
	command = Column(String)
	
class UserSourceTable(BaseMessageSourceTable):
	__tablename__ = 'MessageSource_User'
	user_name = Column(String)