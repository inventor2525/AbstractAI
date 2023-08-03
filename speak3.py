from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import torch
import soundfile as sf
from Stopwatch import Stopwatch

class TextToSpeech:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.sw = Stopwatch()

    def text_to_speech(self, text:str, file_path:str):
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

    def text_to_speech(self, text:str, file_path:str="speech.wav"):
        self.sw.start("text to speech")
        inputs = self.processor(text=text, return_tensors="pt")
        inputs = {name: tensor.to(self.device) for name, tensor in inputs.items()}
        speech = self.model.generate_speech(inputs["input_ids"], self.speaker_embeddings, vocoder=self.vocoder)
        speech = speech.cpu()
        sf.write(file_path, speech.numpy(), samplerate=16000)
        self.sw.stop("text to speech")

tts = MicrosoftSpeechT5TTS()

tts.text_to_speech(
    "Hello! I am a computer. Do you understand english like I do? If so, can you see how well I am handling punctuation? What about my pauses? Or my grammar?",
    "file_1.wav"
)
tts.text_to_speech(
    "What if I am running on the Gee Pee yoU versus the (C) (P) (U)? Do you still understand me then? That would be good if you did because this thing is fairly slow to run on the [C] [P] [U]. ",
    "file_2.wav"
)
tts.text_to_speech(
    "I still as a computer however, do not do well, as you can see, reading acrynyms. Things like See, pea, you? arent read well when you type CPU.",
    "file_3.wav"
)
