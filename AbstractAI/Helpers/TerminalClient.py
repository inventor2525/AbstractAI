# Terminal client class.
#
# For the server class under a different license, see:
# https://github.com/inventor2525/AbstractAI_Terminal

from AbstractAI.Helpers.TerminalData import *
from ClassyFlaskDB.new.FlaskifyDecorator import FlaskifyDecorator
from typing import List

TerminalFLASKIFY = FlaskifyDecorator(DATA)

@TerminalFLASKIFY
class Terminal:
	def __init__(self, name:str, columns: int = 80, main_lines:int = 10000, lines: int = 24):
		pass
	
	@TerminalFLASKIFY.route
	def getScreenDump(self) -> ScreenDump:
		pass
	
	@TerminalFLASKIFY.route
	def send_string(self, data: str):
		pass

	@TerminalFLASKIFY.route
	def write_bytes(self, data: bytes):
		pass

	@TerminalFLASKIFY.route
	def get_output(self) -> List[Output]:
		pass

	@TerminalFLASKIFY.route
	def get_cursor_position(self) -> Vector2:
		pass

	@TerminalFLASKIFY.route
	def close(self):
		pass

if __name__ == '__main__':
	TerminalFLASKIFY.make_client('localhost', 7788)
	
	t = Terminal("bash")
	import time
	time.sleep(2)
	print(t.getScreenDump().raw_text)
	t.send_string('nano\n')
	
	time.sleep(2)
	print(t.getScreenDump().raw_text)
	
	outputs = t.get_output()
	print("".join([o.string for o in outputs]))