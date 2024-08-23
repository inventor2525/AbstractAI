from AbstractAI.Automation.Agent import Agent
from AbstractAI.Model.Converse import Conversation, Message, Role
from AbstractAI.Helpers.ResponseParsers import extract_code_blocks, MarkdownCodeBlockInfo
from AbstractAI.Conversable import Conversable
from jinja2 import Template
import subprocess
import os
from typing import Tuple, Optional, Iterator, Callable

class MainAgent(Agent):
    def __call__(self, conversation: Optional[Conversation] = None) -> Conversation:
        stack_trace = CallerInfo.catch([0,1])
        main_agent_conv = Conversation("Main Agent", "Executes instructions and modifies files") | self.config | stack_trace
        
        if conversation is not None:
            main_agent_conv.props.previous_conversation = conversation
            system_message = f"You were talking previously. This is what was said:\n\n{str(conversation)}"
            main_agent_conv + (system_message, Role.System()) | stack_trace
        
        return main_agent_conv

    def chat(self, conversation: Conversation, start_str: str = "", stream: bool = False, max_tokens: Optional[int] = None) -> Message:
        conversation - MainAgent.conversation_template
        conversation + (MainAgent.conversation_template.render(), Role.System())
        
        response = self.llm.chat(conversation, start_str=start_str, stream=stream, max_tokens=max_tokens)
        
        return response

    def process_response(self, conversation: Conversation) -> Iterator[Tuple[MarkdownCodeBlockInfo, Optional[Callable[[], subprocess.Popen]]]]:
        last_message = conversation[-1]
        code_blocks = extract_code_blocks(last_message.content)
        
        for code_block in code_blocks:
            if code_block.path:
                yield code_block, None
                
                # Save file
                os.makedirs(os.path.dirname(code_block.path), exist_ok=True)
                with open(code_block.path, 'w', encoding='utf-8') as file:
                    file.write(code_block.content)
            elif code_block.language == 'bash':
                def get_process() -> subprocess.Popen:
                    return subprocess.Popen(
                        ['bash', '-c', code_block.content],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                yield code_block, get_process
            else:
                # Other code blocks (for future implementation)
                yield code_block, None

MainAgent.conversation_template = Template("""
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

Note that the order of these instructions is important. If you modify a file, then run a bash command, then modify another file, the changes will occur in that order. You can use bash commands to validate that your changes have occurred as expected.
""")