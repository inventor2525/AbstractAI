from .UserSource import UserSource, ConversationDATA

@ConversationDATA
class FilesSource(UserSource):
	'''Describes the source of a message from a person.'''
	files:dict