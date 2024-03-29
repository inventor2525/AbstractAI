from typing import List
from ClassyFlaskDB.Flaskify import StaticRoute, Flaskify
from ClassyFlaskDB.DATA import DATAEngine

from AbstractAI.ConversationModel import *
from AbstractAI.SpeechToText.SpeechToText import SpeechToText
from AbstractAI.TextToSpeech.TextToSpeech import TextToSpeech
from AbstractAI.LLMs.ModelLoader import ModelLoader
from AbstractAI.LLMs.LLM import LLM

from typing import Dict
from AbstractAI.Helpers.nvidia_smi import nvidia_smi
from pydub import AudioSegment
import re

# Finish creating the conversation model:
data_engine = DATAEngine(ConversationDATA)

@Flaskify
class System():
	whisper : SpeechToText
	tts : TextToSpeech
	LLMs : Dict[str,LLM] = {}
	model_loader : ModelLoader
	
	@Flaskify.ServerInit
	def start_server():
		from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT
		from AbstractAI.TextToSpeech.MicrosoftSpeechT5_TTS import MicrosoftSpeechT5_TTS
		
		# System.whisper = WhisperSTT()
		# System.whisper.load_model("large")

		# System.tts = MicrosoftSpeechT5_TTS()
		
		# System.model_loader = ModelLoader()
	
	##################################################
	## System
	##################################################
	@StaticRoute
	def server_nvidia_smi() -> str:
		return nvidia_smi()

	##################################################
	## Speech to Text
	##################################################
	@StaticRoute
	def load_STT_model(stt_model_name:str) -> None:
		System.whisper.load_model(stt_model_name)
	
	@StaticRoute
	def list_STT_models() -> list:
		return System.whisper.list_models()
	
	@StaticRoute
	def transcribe(audio:AudioSegment) -> dict:
		return System.whisper.transcribe(audio)
	
	@StaticRoute
	def transcribe_str(audio:AudioSegment) -> str:
		return System.whisper.transcribe_str(audio)
	
	##################################################
	## Text to Speech
	##################################################		
	@StaticRoute
	def speak(text:str) -> AudioSegment:
		separated_text,_ = TextToSpeech.split_codeblocks(text)
		return System.tts.text_to_speech(separated_text)
	
	##################################################
	## LLM
	##################################################
	@StaticRoute
	def list_LLMs() -> List[str]:
		return System.LLMs.keys()
	
	@StaticRoute
	def load_LLM(llm_name:str) -> None:
		if llm_name not in System.LLMs:
			llm = System.model_loader[llm_name]
			llm.start()
			System.LLMs[llm_name] = llm
	
	@staticmethod
	def get_llm(llm_name:str) -> LLM:
		if llm_name not in System.LLMs:
			System.load_LLM(llm_name)
		return System.LLMs[llm_name]
	
	@StaticRoute
	def unload_LLM(llm_name:str) -> None:
		if llm_name in System.LLMs:
			del System.LLMs[llm_name]
	
	@StaticRoute
	def prompt_str(llm_name:str, prompt:str) -> Message:
		return System.LLMs[llm_name].prompt_str(prompt).message
	
	@StaticRoute
	def prompt_chat(llm_name:str, conversation:Conversation, start_str:str) -> Message:
		print_conversation(conversation)
		response = System.get_llm(llm_name).prompt(conversation, start_str)
		print(f"Tokens in response: {response.token_count}")
		print(f"Response: {response.message.content}")
		conversation.new_message_sequence()
		conversation.add_message(response.message)
		return response.message