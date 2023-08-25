wget -nc https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b
eval "$(/home/ubuntu/miniconda3/bin/conda shell.bash hook)"
printf '\neval "$(/home/ubuntu/miniconda3/bin/conda shell.bash hook)"' >> ~/.bashrc
conda create -n py10 python=3.10 -y
conda activate py10
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y
pip install einops;
pip install transformers;
pip install accelerate;
pip install sentencepiece;
pip install --upgrade numexpr;
pip install openai-whisper;
pip install datasets;
pip install soundfile;
cd StableBeluga2-70B-Chat/;
pip install -r requirements.txt;
cd ..
nano oa_py6_9.py
git clone https://github.com/LAION-AI/Open-Assistant.git
cd Open-Assistant/
git checkout v0.0.3-alpha36
cd model/
pip install -e .
pip install -e .
history