#!/bin/bash

# Get the start time
start_time=$(date +"%Y%m%d%H%M%S")

# Define the log file
log_file="log_${start_time}.txt"

# List of model names
model_names=(
"OpenAssistant/falcon-7b-sft-mix-2000"
"OpenAssistant/llama2-13b-orca-v2-8k-3166"
"OpenAssistant/oasst-sft-1-pythia-12b"
"OpenAssistant/oasst-rm-2-pythia-6.9b-epoch-1"
"OpenAssistant/falcon-40b-sft-mix-1226" 
"OpenAssistant/falcon-40b-sft-top1-560" 
)

# Loop over each model name and call the Python script
for model_name in "${model_names[@]}"
do
  python3 OpenAssistant.py --model_name $model_name | tee -a $log_file
done
