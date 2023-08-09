from Stopwatch import Stopwatch
from pydub import AudioSegment
import torch

class TextToSpeech:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.sw = Stopwatch()

    def text_to_speech(self, text:str) -> AudioSegment:
        raise NotImplementedError