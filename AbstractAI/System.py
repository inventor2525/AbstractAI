from dataclasses import dataclass, field
from typing import List
from ClassyFlaskDB.Flaskify import StaticRoute, Flaskify
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT
from AbstractAI.TextToSpeech.MicrosoftSpeechT5_TTS import MicrosoftSpeechT5_TTS, TextToSpeech
from AbstractAI.LLMs.LoadLLM import *
from pydub import AudioSegment
import re

@Flaskify()
class System():
	whisper : WhisperSTT
	tts : MicrosoftSpeechT5_TTS
	LLMs : dict = {}

	@staticmethod
	def start_server():
		System.whisper = WhisperSTT()
		System.whisper.load_model("large")

		System.tts = MicrosoftSpeechT5_TTS()

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
			System.LLMs[llm_name] = LoadLLM(llm_name)
	
	@StaticRoute()
	def unload_LLM(llm_name:str) -> None:
		if llm_name in System.LLMs:
			del System.LLMs[llm_name]
	
	@StaticRoute()
	def prompt_str(llm_name:str, prompt:str) -> Message:
		return System.LLMs[llm_name].prompt_str(prompt).message