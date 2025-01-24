from AbstractAI.ApplicationCore import *

appCore = ApplicationCore("/home/charlie/Documents/AbstractAI")
	
def transcription_completed(transcription:Transcription):
	print(f"Transcribed: '{transcription.text}' at {datetime.now()}")
appCore.transcription_completed.connect(transcription_completed)

try:
	appCore.audio_recorder.start_recording()
	appCore.vad.start()
	print("VAD started. Press Ctrl+C to stop.")

	# Detect audio segments where there is human voice:
	for audio in appCore.vad.voice_segments():
		print(f"\nDetected voice segment of length: {audio.length} ms at {datetime.now()}")
		
		# Transcribe each of them live:
		AppContext.jobs.add(TranscriptionJob(
			job_key="Transcribe", audio=audio
		))

except KeyboardInterrupt:
	print("Stopping VAD...")
finally:
	appCore.vad.stop()
	all_audio = appCore.audio_recorder.stop_recording()
	# Save to file or do what ever with all the audio for training purposes etc
	appCore.audio_recorder.stop_listening()
	print("VAD stopped.")