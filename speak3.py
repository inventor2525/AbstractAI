from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import torch
import soundfile as sf

# Check if CUDA is available and set the device to GPU if it is
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Using device: {device}')  # This will print 'cuda' if CUDA is available

processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts").to(device)  # Move the model to the GPU
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to(device)  # Move the vocoder to the GPU

# load xvector containing speaker's voice characteristics from a dataset
embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0).to(device)  # Move the embeddings to the GPU

def text_to_speach(text:str, file_path:str="speech.wav"):
    print("Running...")
    inputs = processor(text=text, return_tensors="pt")

    # Move the inputs to the GPU
    inputs = {name: tensor.to(device) for name, tensor in inputs.items()}

    speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)

    # Move the speech tensor back to CPU for saving to file
    speech = speech.cpu()

    sf.write(file_path, speech.numpy(), samplerate=16000)
    print("Done")

text_to_speach(
    "Hello! I am a computer. Do you understand english like I do? If so, can you see how well I am handling punctuation? What about my pauses? Or my grammar?",
    "file_1.wav"
)
text_to_speach(
    "What if I am running on the Gee Pee yoU versus the (C) (P) (U)? Do you still understand me then? That would be good if you did because this thing is fairly slow to run on the [C] [P] [U]. ",
    "file_2.wav"
)

text_to_speach(
    "I still as a computer however, do not do well, as you can see, reading acrynyms. Things like See, pea, you? arent read well when you type CPU.",
    "file_3.wav"
)