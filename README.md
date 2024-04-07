# AbstractAI

Abstracts away various LLMs and provides a simple local Qt chat interface to interact with them, while focusing on the users ability to modify any part of a conversation with traceability.

Using ClassyFlaskDB, all interactions with LLMs and any modifications made to a conversation with them are logged with detailed source information to aid in filtering them for future training data.

This also implements speech to text as a type anywhere input method and several examples on text to speech using local models or a user deployed server.

## Installation

1. pip install ClassyFLaskDB from here: https://github.com/inventor2525/ClassyFlaskDB
1. pip install AbstractAI from this repo
3. Add model definitions to models.json (directions to come)
## Usage

### Linux
#### Chat Interface

```bash
cd <path to AbstractAI>
python AbstractAI/UI/main.py
```
Add models to models.json in ~/.config/AbstractAI/ to use them in the chat interface.
Config screen to come.

#### Speech to Text
Requires a server or modification to run locally.

Provides a simple interface to type anywhere using speech to text using a simple indicator in the top left of the screen.

Modify it to use a different key combo for transcribing using evtest to find the key codes, or simply left click the circle icon in the top left corner of the screen to toggle recording.

Common transcription APIs are not yet supported. This was built before they came out.

##### No-feedback mode
Transcribes all at once after user exits transcribe mode
```bash
cd <path to AbstractAI>
python AbstractAI/examples/record_keys.py
```

##### Talk typing feedback
Transcribes incrementally as the user speaks, using a small local model to provide feedback on what is being transcribed and a larger local or remote model to provide the final transcription.

```bash
cd <path to AbstractAI>
python AbstractAI/examples/record_keys2.py
```
