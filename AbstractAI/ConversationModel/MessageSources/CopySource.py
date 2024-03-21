from .MessageSource import MessageSource
# from AbstractAI.ConversationModel.ModelBase import *
from typing import List

# @ConversationDATA
from dataclasses import dataclass, field
@dataclass
class CopySource(MessageSource):
	"""The source of a message coppied from n other messages."""

	sources: List["Message"] = field(default_factory=list)