import asyncio
import os
import pty
import signal
import subprocess
import re

class Terminal:
	def __init__(self):
		self.master, self.slave = pty.openpty()
		self.process = subprocess.Popen(
			["bash"],
			stdin=self.slave,
			stdout=self.slave,
			stderr=self.slave,
			bufsize=0,
			preexec_fn=os.setsid,
		)
		
	async def _read_output(self):
		"""Clean the output from the terminal."""
		loop = asyncio.get_event_loop()
		output = await loop.run_in_executor(None, os.read, self.master, 1024)
		decoded_output = output.decode()
		ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
		cleaned_output = ansi_escape.sub('', decoded_output)
		extra_characters = re.compile(r'(\x07|^0;[^$]*)(?=.*?@)')
		return extra_characters.sub('', cleaned_output)
		
	async def run_command(self, command:str, timeout:float=None)->str:
		"""Run the passed command and return the output."""
		
		os.write(self.master, f"{command}\n".encode())

		lines = []
		while True:
			try:
				line = await asyncio.wait_for(self._read_output(), timeout)
				if line:
					lines.append(line.rstrip())
				else:
					break
			except asyncio.TimeoutError:
				print("Command timed out")
				await self.stop()
				break

		return "\n".join(lines)

	async def stop(self):
		"""Stop any running command"""
		os.killpg(os.getpgid(self.process.pid), signal.SIGINT)