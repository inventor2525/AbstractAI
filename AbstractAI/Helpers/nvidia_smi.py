import subprocess

def nvidia_smi() -> str:
	'''returns nvidia-smi output'''
	return subprocess.check_output(["nvidia-smi"]).decode()