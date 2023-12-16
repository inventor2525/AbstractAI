from dataclasses import dataclass, field
from typing import List
from ClassyFlaskDB.Flaskify import StaticRoute, Flaskify
from ClassyFlaskDB.DATA import DATAEngine
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT
from AbstractAI.TextToSpeech.MicrosoftSpeechT5_TTS import MicrosoftSpeechT5_TTS, TextToSpeech
from AbstractAI.Helpers.nvidia_smi import nvidia_smi
from AbstractAI.LLMs.LoadLLM import *
from pydub import AudioSegment
import re

# Finish creating the conversation model:
data_engine = DATAEngine(DATA)

@Flaskify()
class System():
	whisper : WhisperSTT
	tts : MicrosoftSpeechT5_TTS
	LLMs : Dict[str,LLM] = {}

	@staticmethod
	def start_server():
		System.whisper = WhisperSTT()
		System.whisper.load_model("large")

		System.tts = MicrosoftSpeechT5_TTS()

	##################################################
	## System
	##################################################
	@StaticRoute()
	def server_nvidia_smi() -> str:
		return nvidia_smi()

	##################################################
	## Speech to Text
	##################################################
	@StaticRoute()
	def load_STT_model(stt_model_name:str) -> None:
		System.whisper.load_model(stt_model_name)
	
	@StaticRoute()
	def list_STT_models() -> list:
		return System.whisper.list_models()
	
	@StaticRoute()
	def transcribe(audio:AudioSegment) -> str:
		return System.whisper.transcribe_str(audio)
	
	##################################################
	## Text to Speech
	##################################################		
	@StaticRoute()
	def speak(text:str) -> AudioSegment:
		separated_text,_ = TextToSpeech.split_codeblocks(text)
		return System.tts.text_to_speech(separated_text)
	
	##################################################
	## LLM
	##################################################
	@StaticRoute()
	def list_LLMs() -> List[str]:
		return System.LLMs.keys()
	
	@StaticRoute()
	def load_LLM(llm_name:str) -> None:
		if llm_name not in System.LLMs:
			llm = LoadLLM(llm_name)
			llm.start()
			System.LLMs[llm_name] = llm
	
	@StaticRoute()
	def unload_LLM(llm_name:str) -> None:
		if llm_name in System.LLMs:
			del System.LLMs[llm_name]
	
	@StaticRoute()
	def prompt_str(llm_name:str, prompt:str) -> Message:
		return System.LLMs[llm_name].prompt_str(prompt).message
	
	@StaticRoute()
	def prompt_chat(llm_name:str, conversation:Conversation) -> Message:
		print_conversation(conversation)
		response = System.LLMs[llm_name].prompt(conversation)
		print(f"Tokens in response: {response.token_count}")
		conversation.new_message_sequence()
		conversation.add_message(response.message)
		return response.message