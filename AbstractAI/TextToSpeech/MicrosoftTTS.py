from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
from .TextToSpeech import *

class MicrosoftSpeechT5_TTS(TextToSpeech):
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