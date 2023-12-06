from flask import Flask
from ClassyFlaskDB.Flaskify import Flaskify

app = Flask(__name__)
Flaskify.make_server(app)

from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT

if __name__ == '__main__':
    app.run(port=8000)