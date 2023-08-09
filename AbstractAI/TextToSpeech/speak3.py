from AbstractAI.Helpers.AudioPlayer import *
from AbstractAI.TextToSpeech.MicrosoftTTS import *

ap = AudioPlayer()

tts = MicrosoftSpeechT5_TTS()

s1 = tts.text_to_speech(
    "Hello! I am a computer. Do you understand english like I do? If so, can you see how well I am handling punctuation? What about my pauses? Or my grammar?"
)
s1.export("file_1.wav", format="wav")
ap.play(s1)

s2 = tts.text_to_speech(
    "What if I am running on the Gee Pee yoU versus the (C) (P) (U)? Do you still understand me then? That would be good if you did because this thing is fairly slow to run on the [C] [P] [U]. "
)
s2.export("file_2.wav", format="wav")
ap.play(s2)

s3 = tts.text_to_speech(
    "I still as a computer however, do not do well, as you can see, reading acrynyms. Things like See, pea, you? arent read well when you type CPU."
)
s3.export("file_3.wav", format="wav")
ap.play(s3)