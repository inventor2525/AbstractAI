import pexpect
import asyncio
import re

class Terminal:
	def __init__(self, docker_container_name:str=None, anonymize:bool=True):
		command = "/bin/bash"
		if docker_container_name is not None:
			command = f"docker run -it {docker_container_name} /bin/bash"
		self.output_history = ''
		self.pattern = r'([a-zA-Z0-9_.-]+)@([a-zA-Z0-9_.-]+):([^$#]*)([#$] )'
		self.anonymize = anonymize
		
		self.child = pexpect.spawn(command, encoding='utf-8')
		self.output_history = self._get_output()
		
	def _clean_response(self, text:str)->str:
		text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters
		text = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)  # Remove escape sequences
		
		# Fix the "user@computer:PWD$ ":
		text = re.sub(r'0;(.+?: .+)\x07', '', text)
		return text
			
	def _get_output(self, timeout:float=None):
		self.child.expect([self.pattern], timeout=timeout)
		response = self._clean_response(
			self.child.before + self.child.match.group(0)
		).replace('\r\n', '\n')
		if self.anonymize:
			response = re.sub(self.pattern, r"user@computer:\3\4", response)
		return response
		
	async def run_command(self, command, timeout:float=None):
		self.child.sendline(command)
		response = self._get_output()
		
		self.output_history += response
		return response.removeprefix(f"{command}\n")
	
	def run_command_blocking(self, command, timeout:float=None):
		return asyncio.run(self.run_command(command, 30))
		
	async def stop(self):
		"""Stop any running command"""
		os.killpg(os.getpgid(self.child.pid), signal.SIGINT)

# Example usage
if __name__ == '__main__':
	def log_print(user_input:str, response:str):
		print(response)
		with open('terminal_log.txt', 'a') as file:
			file.write(f"{user_input}\n{response}")
	
	terminal = Terminal()
	log_print("", terminal.output_history)
	
	inputs = [
		"cd ~",
		"rm -rf test_thing1",
		"mkdir test_thing1",
		"cd test_thing1",
		"touch bla",
		"git init",
		"git add bla",
		"git commit -m \"Test\"",
		"ls -a"
	]
	
	for inpt in inputs:
		user_input = inpt
		response = terminal.run_command_blocking(user_input)
		log_print(user_input, response)
	while True:
		user_input = input()
		response = terminal.run_command_blocking(user_input)
		log_print(user_input, response)