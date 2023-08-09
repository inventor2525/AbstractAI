import queue
import threading
from pydub import AudioSegment
from pydub.playback import play

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