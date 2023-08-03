from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import torch
import soundfile as sf
from Stopwatch import Stopwatch

import queue
import threading
from pydub import AudioSegment
from pydub.playback import play

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



class AudioPlayer:
    def __init__(self):
        self.queue = queue.Queue()
        self.playing = False
        self.thread = threading.Thread(target=self.run)

    def play(self, audio:AudioSegment) -> None:
        self.queue.put(audio)
        if not self.playing:
            self.thread.start()

    def run(self):
        self.playing = True
        while self.playing:
            if not self.queue.empty():
                audio = self.queue.get()
                play(audio)
            else:
                self.playing = False

    def stop(self):
        while not self.queue.empty():
            self.queue.get()
        self.playing = False

ap = AudioPlayer()

tts = MicrosoftSpeechT5TTS()

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

ap.play(s1)
ap.play(s2)
ap.play(s3)