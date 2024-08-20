from AbstractAI.Automation.Agent import Agent, CallerInfo, Role
from AbstractAI.Model.Converse import Conversation, Message
from AbstractAI.Helpers.ResponseParsers import extract_paths_and_code
from jinja2 import Template
import subprocess
import os
from datetime import datetime

class MainAgent(Agent):
    def __call__(self, conversation: Conversation) -> Conversation:
        stack_trace = CallerInfo.catch([0,1])
        
        main_agent_conv = Conversation("Main Agent", "Executes instructions and modifies files") | self.config
        main_agent_conv + (
            MainAgent.conversation_template.render(
                conversation=str(conversation)
            ),
            Role.System()
        ) | stack_trace
        
        main_agent_conv + ("Now, provide instructions for file modifications and bash commands.", Role.User()) | stack_trace
        return main_agent_conv

    def process_response(self, conversation: Conversation):
        last_message = conversation[-1]
        message_id = last_message.get_primary_key()
        
        # Process file modifications
        for path, code in extract_paths_and_code(last_message.content):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as file:
                file.write(code)
        
        # Process bash blocks
        bash_blocks = self.extract_bash_blocks(last_message.content)
        for i, bash_block in enumerate(bash_blocks, 1):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
            script_filename = f"{timestamp}_{message_id}_{i}"
            script_path = os.path.expanduser(f"~/ai_scripts/{script_filename}")
            
            os.makedirs(os.path.dirname(script_path), exist_ok=True)
            
            with open(script_path, 'w') as f:
                f.write(bash_block)
            
            output_filename = f"{script_filename}_output"
            output_path = os.path.expanduser(f"~/ai_scripts/{output_filename}")
            
            process = subprocess.Popen(['bash', script_path], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.STDOUT, 
                                       text=True, 
                                       bufsize=1, 
                                       universal_newlines=True)
            
            with open(output_path, 'w') as output_file:
                for line in process.stdout:
                    output_file.write(line)
            
            process.wait()

    def extract_bash_blocks(self, content):
        # This is a simple implementation. You might need to adjust it based on your exact markdown format.
        bash_blocks = []
        lines = content.split('\n')
        in_bash_block = False
        current_block = []

        for line in lines:
            if line.strip() == '```bash':
                in_bash_block = True
            elif line.strip() == '```' and in_bash_block:
                in_bash_block = False
                bash_blocks.append('\n'.join(current_block))
                current_block = []
            elif in_bash_block:
                current_block.append(line)

        return bash_blocks

MainAgent.conversation_template = Template("""
You are an AI assistant capable of modifying files and executing bash commands. Your task is to provide instructions for file modifications and bash commands based on the user's request.

Here's how you can use the tools provided:

1. To modify or create a file, specify the file path followed by a code block. For example:
   /path/to/file.py
   ```python
   print("Hello, World!")
   ```

2. To execute bash commands, use a bash code block. For example:
   ```bash
   echo "Hello from bash!"
   ls -l
   ```

You can combine file modifications and bash commands in any order. Make sure to provide clear and concise instructions.

Here's the current conversation for context:
==============
{{ conversation }}
==============

Now, based on the user's request, provide instructions for file modifications and bash commands.
""")