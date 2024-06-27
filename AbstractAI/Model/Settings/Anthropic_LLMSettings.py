from .LLMSettings import *

@DATA(generated_id_type=ID_Type.HASHID)
@dataclass
class Anthropic_LLMSettings(LLMSettings):
    __ui_name__ = "Anthropic"
    model_name: str = "claude-3-5-sonnet-20240620"
    api_key: str = ""
    
    def load(self):
        from AbstractAI.LLMs.Anthropic_LLM import Anthropic_LLM
        return Anthropic_LLM(self.copy())