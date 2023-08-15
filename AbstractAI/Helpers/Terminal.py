import pexpect
import asyncio
import re

class Terminal:
	def __init__(self):
		self.child = pexpect.spawn('/bin/bash', encoding='utf-8')
		self.output_history = ''
		self.child.expect(['\$', '#'], timeout=None)
		self.run_command_blocking('pwd')  # Get the working directory at start
		
		response = self.output_history.strip().split('\r\n')[2]
		self.output_history = response + '\n'
		
	async def run_command(self, command, timeout:float=None):
		self.child.sendline(command)
		self.child.expect(['\$ '], timeout=timeout)
		response = self.child.before
		response = re.sub(r'[^\x00-\x7F]+', '', response)  # Remove non-ASCII characters
		response = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', response)  # Remove escape sequences
		
		response = re.sub(r'0;(.+?: .+)\x07', '', response)
		response = f"{response}$ "
		self.output_history += response  # Append to output history
		return response
	
	def run_command_blocking(self, command, timeout:float=None):
		return asyncio.run(self.run_command(command, 2))
		
	async def stop(self):
		"""Stop any running command"""
		os.killpg(os.getpgid(self.child.pid), signal.SIGINT)

# Example usage
if __name__ == '__main__':
	terminal = Terminal()
	print(terminal.output_history)
	with open('terminal_log.txt', 'a') as file:
		file.write(terminal.output_history)
		
	while True:
		user_input = input()
		response = terminal.run_command_blocking(user_input)
		print(response)
		
		with open('terminal_log.txt', 'a') as file:
			file.write(response)