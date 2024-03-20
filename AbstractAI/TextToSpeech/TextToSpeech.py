from AbstractAI.Helpers.Stopwatch import Stopwatch
from abc import ABC, abstractmethod
from pydub import AudioSegment
import re

class TextToSpeech(ABC):
	def __init__(self):
		import torch
		self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
		self.sw = Stopwatch()

	@abstractmethod
	def text_to_speech(self, text:str) -> AudioSegment:
		pass
	
	@staticmethod
	def split_codeblocks(text):
		'''Separates out the code blocks from input text.'''
		pattern = r'```^(\w+)?$'
		inside_code_block = False
		delimiter_count = 0
		regular_text = ''
		code_blocks = []
		code_block_content = ''
		for line in text.split('\n'):
			match = re.match(pattern, line)
			if match:
				if match.group(1):  # Start of a code block
					delimiter_count += 1
					inside_code_block = True
					language = match.group(1) if match.group(1) else ''
				else:  # End of a code block
					delimiter_count -= 1
					if delimiter_count == 0:
						inside_code_block = False
						code_blocks.append(code_block_content.strip())
						regular_text += 'Some ' + language + ' code\n'
						code_block_content = ''
			if inside_code_block:
				code_block_content += line + '\n'
			else:
				regular_text += line + '\n'
		return regular_text, code_blocks