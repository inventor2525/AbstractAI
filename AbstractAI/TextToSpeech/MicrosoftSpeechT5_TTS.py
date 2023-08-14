from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from nltk.tokenize import sent_tokenize, word_tokenize
from datasets import load_dataset
from .TextToSpeech import *
import nltk

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
		MAX_TOKEN_LENGTH = 600  # Set according to the model's constraints

		# Break the text into sentences and words
		sentences = sent_tokenize(text)
		speech_segments = []
		group = []
		token_count = 0

		def generate_speech_for_group(group):
			group_text = " ".join(group)
			inputs = self.processor(text=group_text, return_tensors="pt")
			inputs = {name: tensor.to(self.device) for name, tensor in inputs.items()}
			speech = self.model.generate_speech(inputs["input_ids"], self.speaker_embeddings, vocoder=self.vocoder)
			speech = speech.cpu()
			return (speech * 32767).numpy().astype('int16')

		for sentence in sentences:
			words = word_tokenize(sentence)
			for word in words:
				inputs = self.processor(text=word, return_tensors="pt")
				input_ids = inputs["input_ids"]
				new_token_count = token_count + len(input_ids[0])

				if new_token_count <= MAX_TOKEN_LENGTH:
					group.append(word)
					token_count = new_token_count
				else:
					# Generate speech for the current group and start a new group
					speech_segments.append(generate_speech_for_group(group))
					group = [word]
					token_count = len(input_ids[0])

		# Handle the last group
		if group:
			speech_segments.append(generate_speech_for_group(group))

		# Concatenate all the speech segments
		full_speech = np.concatenate(speech_segments, axis=0)

		return AudioSegment(
			data=full_speech.tobytes(),
			sample_width=2,
			frame_rate=16000,
			channels=1,
		)