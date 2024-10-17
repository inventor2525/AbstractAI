from pyannote.audio import Model
from pyannote.audio.pipelines import VoiceActivityDetection
import threading
import time
import numpy as np
import torch
from AbstractAI.Helpers.AudioRecorder import AudioRecorder

class VAD:
	def __init__(self, peek_interval=0.5):
		self.recorder = AudioRecorder()
		self.peek_interval = peek_interval
		self.running = False
		self.vad_thread = None

		# Initialize the model
		self.model = Model.from_pretrained(
			"pyannote/segmentation-3.0", 
			use_auth_token="")

		# Initialize the pipeline
		self.pipeline = VoiceActivityDetection(segmentation=self.model)
		HYPER_PARAMETERS = {
			"min_duration_on": 0.0,
			"min_duration_off": 0.0
		}
		self.pipeline.instantiate(HYPER_PARAMETERS)

	def start(self):
		if not self.running:
			self.running = True
			self.recorder.start_recording()
			self.vad_thread = threading.Thread(target=self._vad_loop)
			self.vad_thread.start()

	def stop(self):
		if self.running:
			self.running = False
			self.vad_thread.join()
			self.recorder.stop_recording()
			self.recorder.stop_listening()

	def _vad_loop(self):
		while self.running:
			time.sleep(self.peek_interval)
			audio_data = self.recorder.peak(return_type=np.ndarray)
			if audio_data.size > 0:
				self._process_audio(audio_data)

	def _process_audio(self, audio_data):
		# Convert numpy array to torch tensor
		waveform = torch.from_numpy(audio_data).float().t()
		
		# Ensure the shape is (channel, time)
		if waveform.dim() == 1:
			waveform = waveform.unsqueeze(0)  # Add channel dimension
		elif waveform.dim() == 2 and waveform.shape[0] > waveform.shape[1]:
			waveform = waveform  # Transpose if shape is (time, channel)
		
		# Process the audio
		vad_result = self.pipeline({
			'waveform': waveform, 
			'sample_rate': self.recorder.sample_rate
		})
		
		print(f"VAD Result: {vad_result}")

# Test script
if __name__ == "__main__":
	vad = VAD(peek_interval=0.5)
	try:
		vad.start()
		print("VAD started. Press Ctrl+C to stop.")
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print("Stopping VAD...")
	finally:
		vad.stop()
		print("VAD stopped.")