from .LLMSettings import *

@DATA(id_type=ID_Type.HASHID)
@dataclass
class Anthropic_LLMSettings(LLMSettings):
    __ui_name__ = "Anthropic"
    model_name: str = "claude-3-5-sonnet-20240620"
    api_key: str = field(default_factory=environ_getter("ANTHROPIC_API_KEY"))
    
    def load(self):
        from AbstractAI.LLMs.Anthropic_LLM import Anthropic_LLM
        return Anthropic_LLM(self.copy())