import argparse
from flask import Flask, request, jsonify
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT

parser = argparse.ArgumentParser(description='Remote Speech-to-Text Server')
parser.add_argument('model_name', type=str, choices=['tiny', 'tiny.en', 'small', 'small.en', 'medium', 'medium.en', 'large'], help='Whisper model size to use for transcription.')
args = parser.parse_args()

app = Flask(__name__)
stt = WhisperSTT(args.model_name)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_file = request.files['audio']
    file_name = 'received.wav'
    audio_file.save(file_name)
    transcription = stt.transcribe_str(file_name)
    return jsonify({'transcription': transcription})

app.run(host='0.0.0.0', port=8000)
