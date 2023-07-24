import sounddevice as sd
import numpy as np
import whisper
import io
import wave

# Variables for model size and chunk length
model_size = "base"  # Other options: "tiny", "small", "medium", "large"
chunk_length = 30  # Length of each chunk in seconds

# Load the Whisper model
print("Loading Whisper model...")
model = whisper.load_model(model_size)

# Define the callback for the stream
def callback(indata, frames, time, status):
    # Convert the raw audio data to a format that Whisper can use
    audio_data = np.int16(indata * 32767).tobytes()

    # Save the audio data to a temporary WAV file
    with wave.open('temp.wav', 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_data)

    # Transcribe the audio data with Whisper
    print("Transcribing audio...")
    result = model.transcribe('temp.wav')
    print(result['text'])

# Calculate the number of frames in each chunk
chunk_frames = int(chunk_length * 16000)  # 16000 samples/second

print("Starting recording...")
for _ in range(10):  # Record 10 chunks for testing
    # Record a chunk of audio
    audio_data = sd.rec(frames=chunk_frames, samplerate=16000, channels=1, dtype='float32')
    sd.wait()  # Wait for the recording to finish

    # Call the callback function to transcribe the chunk
    callback(audio_data, chunk_frames, None, None)
