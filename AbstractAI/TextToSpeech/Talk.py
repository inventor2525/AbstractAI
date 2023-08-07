from transformers import AutoProcessor, AutoModel

print("loading model...")
processor = AutoProcessor.from_pretrained("suno/bark-small")
model = AutoModel.from_pretrained("suno/bark-small")

print("setting up input...")
inputs = processor(
    text=["Hello, my name is Suno. And, uh — and I like pizza. [laughs] But I also have other interests such as playing tic tac toe."],
    return_tensors="pt",
)

print("Generating...")
speech_values = model.generate(**inputs, do_sample=True)

print("Saving wav...")
#save wav:
import scipy

sampling_rate = model.config.sample_rate
scipy.io.wavfile.write("bark_out.wav", rate=sampling_rate, data=speech_values.cpu().numpy().squeeze())

print("Done!")