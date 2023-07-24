import sounddevice as sd
import numpy as np
import io
import wave
import whisper
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal
from Stopwatch import Stopwatch

sw = Stopwatch()

# Variables for model size
model_size = "medium"  # Other options: "tiny", "small", "medium", "large"

# Load the Whisper model
sw.start("Loading Whisper model")
model = whisper.load_model(model_size)
sw.stop("Loading Whisper model")

# Create an InputStream for the microphone
stream = sd.InputStream(samplerate=16000, channels=1, dtype='float32')
stream.start()

# Create a buffer to hold the recorded audio data
buffer = np.array([], dtype='float32')

# Define a QThread for the recording process
class RecordingThread(QThread):
    buffer_updated = pyqtSignal(np.ndarray)

    def run(self):
        global buffer
        while self.isRunning():
            data, _ = stream.read(1024)  # Read 1024 frames from the InputStream
            buffer = np.append(buffer, data)  # Append the data to the buffer
            self.buffer_updated.emit(buffer)

# Create a RecordingThread
recording_thread = RecordingThread()

# Define the callback for the button press event
def on_button_press():
    global buffer
    sw.start("Recording")
    buffer = np.array([], dtype='float32')  # Clear the buffer
    recording_thread.start()  # Start the RecordingThread

# Define the callback for the button release event
def on_button_release():
    recording_thread.terminate()  # Stop the RecordingThread
    rt = sw.stop("Recording")["last"]

    global buffer
    # Convert the buffer to bytes
    audio_data = np.int16(buffer * 32767).tobytes()

    sw.start("Saving")
    # Save the audio data to a temporary WAV file
    with wave.open('temp.wav', 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_data)
    sw.stop("Saving")

    sw.start("Transcribing")
    # Transcribe the audio data with Whisper
    result = model.transcribe('temp.wav')
    tt = sw.stop("Transcribing")["last"]
    
    print(f"Seconds per seconds {rt/tt}")
    print(result['text'])

# Create a PyQt application and button
app = QApplication([])
button = QPushButton('Hold to record')
button.pressed.connect(on_button_press)
button.released.connect(on_button_release)
button.show()

# Run the PyQt event loop
app.exec_()

# Stop the InputStream when the application exits
stream.stop()
