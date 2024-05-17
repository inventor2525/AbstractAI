from .MessageSource import MessageSource
from AbstractAI.Model.Decorator import *
from AbstractAI.Model.Converse.MessageSources.CallerInfo import CallerInfo
from datetime import datetime
import hashlib

@DATA
@dataclass
class HardCodedSource(MessageSource):
	"""
	A hard-coded message source with a primary key that is the
	hash of the message's content and if it is a system message.
	"""
	auto_id: str
	create_time: datetime = field(default_factory=get_local_time)
	# TODO: fake_source:MessageSource = None  to indicate what 'role' this message is faking.
	
	__primary_key_name__ = "auto_id" # Set the id as the same name as MessageSource's auto generated id so that the polymorphic relationship can be created correctly. TODO: make this unnecessary.
	
	@classmethod
	def create(cls, message:"Message", *args, **kwargs) -> "HardCodedSource":
		"""
		Creates a message source from the passed message that is to indicate 
		that it is a hard-coded message by hashing its content and system message
		flag as a primary key.
		"""
		CallerInfo.catch_now(refer_to_next=False)
		
		to_hash = [False, message.content]
		if "system_message" in kwargs:
			to_hash[0] = kwargs["system_message"]
		
		to_hash_str = f"[{', '.join([str(x) for x in to_hash])}]"
		hashed = hashlib.sha256(to_hash_str.encode("utf-8")).hexdigest()
		return cls(*args, auto_id=hashed, **kwargs)