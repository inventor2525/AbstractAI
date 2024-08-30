from AbstractAI.Automation.Agent import Agent
from AbstractAI.Model.Converse import Conversation, Message, Role, CallerInfo
from AbstractAI.Helpers.ResponseParsers import extract_code_blocks, MarkdownCodeBlockInfo
from AbstractAI.Conversable import Conversable
from jinja2 import Template
import subprocess
import os
from typing import Tuple, Optional, Iterator, Callable

class MainAgent(Agent):
    def __call__(self, conversation: Optional[Conversation] = None) -> Conversation:
        stack_trace = CallerInfo.catch([0,1])
        main_agent_conv = Conversation("Main Agent", "Executes instructions and modifies files") | self.config
        
        if conversation is not None:
            main_agent_conv.props.previous_conversation = conversation
            system_message = f"You were talking previously. This is what was said:\n\n{str(conversation)}"
            main_agent_conv + (system_message, Role.System()) | stack_trace
        
        return main_agent_conv

    def chat(self, conversation: Conversation, start_str: str = "", stream: bool = False, max_tokens: Optional[int] = None) -> Message:
        format_reminder = MainAgent.format_reminder.render()
        conversation - format_reminder
        conversation + (format_reminder, Role.System())
        
        response = self.llm.chat(conversation, start_str=start_str, stream=stream, max_tokens=max_tokens)
        
        return response

    def process_response(self, conversation: Conversation) -> Iterator[MarkdownCodeBlockInfo]:
        last_message = conversation[-1]
        code_blocks = extract_code_blocks(last_message.content)
        
        for code_block in code_blocks:
            yield code_block

MainAgent.format_reminder = Template("""
So... To help you do that, I'm going to attach you to a parser for a moment and I want you to respond in a certain format. You are now capable of modifying files and executing bash commands for me automatically.

To do so, you can respond in normal markdown with 1 addition for the path:

For file modifications (1), respond like this:
/path/to/file
```language
file contents
```

And for bash execution (2), respond like this:
```bash
command(s) to execute
```

In (1) the file contents will be parsed from the markdown code block and saved to the path specified, but only if there is a full path with extension and nothing else on that line or between it and the code block.

If no path is specified before the codeblock, it will simply be ignored unless it is a bash code block. If it is a bash codeblock without a path on the line before, it's contents will be saved to a temp sh file and executed by a fresh python subprocess.

You can include any other markdown you wish to talk to me, but any file I asked you to save should have a path specified immediately before. That is all you need to do to tell the parser that it should save that code blocks contents to that path.

Note that if you need to modify a bash file in my file system, it is very important you include a path before the code block so it is treated as a file save operation and not wrongly execute the bash block's contents instead. On the contrary, dont include any temp path of your own before a bash block you wish to be executed, one will be created automatically and it will not be run if you include a path before it.

Also, note that the order of these instructions is the order they will happen. Bash and save operations can be interleaved are processed 1 after the other in a single for loop. You could for instance save some code (see (1)), and commit it (see (2)), and then write over it again (1), and git diff with (2) and see the result.

Notice however, that each bash codeblock gets it's own subprocess call once parsed. So do not count on terminal state being carried over between them. If you cd to a dir for instance in 1 bash block, you will not be in that directory in the second unless you cd again.

You can do this. You can save files. You can commit things by writing a bash code block. You can write a whole series of bash commands as though you're running a shell script. You don't need to ask me for help. You can even set breakpoints in code using bash simply by saying the commands to do it.

You will be informed of the results, you can even tree a dir, see it for yourself and save something where I could only loosely remember the path and then commit your work after you find out for yourself what dir I was talking about specifically.

You got this!
""")