from .MessageSource import MessageSource
from AbstractAI.ConversationModel.ModelBase import *
from datetime import datetime
import hashlib

@ConversationDATA
class HardCodedSource(MessageSource):
	"""A message source representing an edited message."""
	auto_id: str
	create_time: datetime = field(default_factory=get_local_time)
	
	__primary_key_name__ = "auto_id" # Set the id as the same name as MessageSource's auto generated id so that the polymorphic relationship can be created correctly. TODO: make this unnecessary.
	
	@classmethod
	def create(cls, message:"Message", *args, **kwargs) -> "HardCodedSource":
		"""
		Creates a message source from the pass message that is to indicate 
		that it is a hard-coded message by hashing its content as a primary key.
		"""
		to_hash = [False, message.content]
		if "system_message" in kwargs:
			to_hash[0] = kwargs["system_message"]
		
		to_hash_str = f"[{', '.join([str(x) for x in to_hash])}]"
		hashed = hashlib.sha256(to_hash_str.encode("utf-8")).hexdigest()
		return cls(auto_id=hashed, *args, **kwargs)