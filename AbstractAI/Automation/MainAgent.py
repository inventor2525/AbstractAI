from AbstractAI.Automation.Agent import Agent
from AbstractAI.Model.Converse import Conversation, Message, Role
from AbstractAI.Helpers.ResponseParsers import extract_code_blocks, MarkdownCodeBlockInfo
import subprocess
import os
from datetime import datetime
from typing import Tuple, Optional, Generator

class MainAgent(Agent):
    def __call__(self, conversation: Conversation) -> Conversation:
        stack_trace = CallerInfo.catch([0,1])
        
        main_agent_conv = Conversation("Main Agent", "Executes instructions and modifies files") | self.config
        
        # Append instructions at the end of the conversation
        instructions = self.get_instructions()
        main_agent_conv + (instructions, Role.System()) | stack_trace
        
        return main_agent_conv

    def get_instructions(self) -> str:
        return """
        You are an AI assistant capable of modifying files and executing commands.
        When providing instructions, use the following format:

        For file modifications:
        /path/to/file
        ```language
        file contents
        ```

        For command execution:
        ```bash
        command to execute
        ```

        Make sure to provide clear and concise instructions.
        """

    def process_response(self, conversation: Conversation) -> Generator[Tuple[MarkdownCodeBlockInfo, Optional[subprocess.Popen]], None, None]:
        last_message = conversation[-1]
        code_blocks = extract_code_blocks(last_message.content)
        
        for code_block in code_blocks:
            if code_block.path:
                # Save file
                os.makedirs(os.path.dirname(code_block.path), exist_ok=True)
                with open(code_block.path, 'w', encoding='utf-8') as file:
                    file.write(code_block.content)
                yield code_block, None
            elif code_block.language == 'bash':
                # Execute bash command
                process = subprocess.Popen(
                    ['bash', '-c', code_block.content],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                yield code_block, process
            else:
                # Other code blocks (for future implementation)
                yield code_block, None

    def chat(self, conversation: Conversation):
        # Append instructions to the end of the conversation
        instructions = self.get_instructions()
        conversation + (instructions, Role.System())
        
        # Call the LLM's chat method
        response = self.llm.chat(conversation)
        
        # Remove the instructions message
        conversation - instructions
        
        # Add the response to the conversation
        conversation + response