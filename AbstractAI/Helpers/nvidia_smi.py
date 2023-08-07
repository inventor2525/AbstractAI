import subprocess

def nvidia_smi():
	'''Print nvidia-smi output'''
	print("nvidia-smi output:")
	print(subprocess.check_output(["nvidia-smi"]).decode())