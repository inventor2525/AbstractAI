from ClassyFlaskDB.DefaultModel import *
from dataclasses import dataclass
from AbstractAI.Tool import Tool
from typing import Any, Dict

@DATA(excluded_fields=['result'])
@dataclass
class ToolSource(Object):
    tool:Tool
    tool_call_id: str
    function_name: str
    function_args: Dict[str, Any]
    result: Any