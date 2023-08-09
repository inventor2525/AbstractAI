#8448MiB with medium.en whisper and TTS
#13134MiB with large
#5276MiB with small.en
#4152MiB with tiny.en
#3988MiB with no whisper

import numpy as np
import io
import wave
import whisper
import torch
import json

from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import torch
import soundfile as sf

import queue
import threading
from pydub import AudioSegment
from pydub.playback import play

from Stopwatch import Stopwatch
sw = Stopwatch()

class TextToSpeech:
	def __init__(self):
		self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
		self.sw = Stopwatch()

	def text_to_speech(self, text:str) -> AudioSegment:
		raise NotImplementedError

class MicrosoftSpeechT5TTS(TextToSpeech):
	def __init__(self):
		super().__init__()
		self.sw.start("load text to speech")
		self.processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
		self.model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts").to(self.device)
		self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to(self.device)
		embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
		self.speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0).to(self.device)
		self.sw.stop("load text to speech")

	def text_to_speech(self, text:str) -> AudioSegment:
		self.sw.start("text to speech")
		inputs = self.processor(text=text, return_tensors="pt")
		inputs = {name: tensor.to(self.device) for name, tensor in inputs.items()}
		speech = self.model.generate_speech(inputs["input_ids"], self.speaker_embeddings, vocoder=self.vocoder)
		speech = speech.cpu()
		self.sw.stop("text to speech")
		
		# Convert to 16-bit integer format
		speech = (speech * 32767).numpy().astype('int16')
		
		return AudioSegment(
			data=speech.tobytes(),
			sample_width=2,  # Update the sample width to 2 for 16-bit integer data
			frame_rate=16000,
			channels=1,
		)

tts = MicrosoftSpeechT5TTS()

# Variables for model size
model_size = "medium.en"  # Other options: "tiny", "small", "medium", "large"

# Load the Whisper model
sw.start("Loading Whisper model")
model = whisper.load_model(model_size)
sw.stop("Loading Whisper model")

for i in range(0,3):
	s1 = tts.text_to_speech(
		"Hello! I am a computer. Do you understand english like I do? If so, can you see how well I am handling punctuation? What about my pauses? Or my grammar?"
	)
	s1.export("file_1.wav", format="wav")

	s2 = tts.text_to_speech(
		"What if I am running on the Gee Pee yoU versus the (C) (P) (U)? Do you still understand me then? That would be good if you did because this thing is fairly slow to run on the [C] [P] [U]. "
	)
	s2.export("file_2.wav", format="wav")

	s3 = tts.text_to_speech(
		"I still as a computer however, do not do well, as you can see, reading acrynyms. Things like See, pea, you? arent read well when you type CPU."
	)
	s3.export("file_3.wav", format="wav")


def transcribe(file:str):
	sw.start("\n\nTranscribing...")
	# Transcribe the audio data with Whisper
	result = model.transcribe(file, language="English", fp16=torch.cuda.is_available())
	transcription_time = sw.stop("\n\nTranscribing...")["last"]

	from pydub import AudioSegment
	audio = AudioSegment.from_file(file)

	print(f"Seconds per seconds {audio.duration_seconds/transcription_time}")
	print(json.dumps(result, indent=4))

for i in range(0,3):
	transcribe("file_1.wav")
	transcribe("file_2.wav")
	transcribe("file_3.wav")