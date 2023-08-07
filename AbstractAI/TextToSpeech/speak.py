from transformers import AutoProcessor, AutoModel
import torch

# Check if CUDA is available and set the device to GPU if it is
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Using device: {device}')  # This will print 'cuda' if CUDA is available

processor = AutoProcessor.from_pretrained("suno/bark-small")
model = AutoModel.from_pretrained("suno/bark-small").to(device)  # Move the model to the GPU

inputs = processor(
    text=["Hello, I'm a computer talking to you!"],
    return_tensors="pt",
)

print("doing the stuff")
# Move the inputs to the GPU
inputs = {name: tensor.to(device) for name, tensor in inputs.items()}

speech_values = model.generate(**inputs, do_sample=True)

import scipy

sampling_rate = model.generation_config.sample_rate
scipy.io.wavfile.write("bark_out.wav", rate=sampling_rate, data=speech_values.cpu().numpy().squeeze())
print("done")