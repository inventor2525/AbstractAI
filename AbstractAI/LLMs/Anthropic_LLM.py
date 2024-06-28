from .LLM import *
from AbstractAI.Model.Settings.Anthropic_LLMSettings import Anthropic_LLMSettings
from anthropic import Anthropic
import json

class Anthropic_LLM(LLM):
    def __init__(self, settings: Anthropic_LLMSettings):
        self.client = None
        super().__init__(settings)
    
    def _complete_str_into(self, prompt: str, wip_message: Message, stream: bool = False, max_tokens: int = None) -> LLM_Response:
        messages = [{"role": "user", "content": prompt}]
        return self._process_messages(messages, wip_message, stream, max_tokens)
    
    def chat(self, conversation: Conversation, start_str: str = "", stream = False, max_tokens: int = None) -> LLM_Response:
        message_list = self.conversation_to_list(conversation)
        wip_message = self._new_message(json.dumps(message_list, indent=4), conversation, start_str)
        return self._process_messages(message_list, wip_message, stream, max_tokens)
    
    def _process_messages(self, messages: List[Dict[str, str]], wip_message: Message, stream: bool, max_tokens: int) -> LLM_Response:
        response = LLM_Response(wip_message, 0, stream)
        
        try:
            completion = self.client.messages.create(
                model=self.settings.model_name,
                max_tokens=max_tokens if max_tokens is not None else 1024,
                messages=messages,
                stream=stream
            )
            
            if stream:
                response.stop_streaming_func = completion.close
                def generate_more_func():
                    try:
                        event = next(completion)
                        print(f"Event type: {event.type}")
                        print(f"Event content: {event.model_dump_json(indent=2)}")
                        
                        if event.type == "message_start":
                            response.input_token_count = event.message.usage.input_tokens
                        elif event.type == "content_block_start":
                            pass  # Initialize any necessary structures
                        elif event.type == "content_block_delta":
                            content = event.delta.text
                            response.add_response_chunk(content, 1, event.model_dump())
                        elif event.type == "message_delta":
                            # Handle any message-level updates
                            pass
                        elif event.type == "content_block_stop":
                            # Finalize any content block processing
                            pass
                        elif event.type == "message_stop":
                            # Finalize message processing
                            return False
                        return True
                    except StopIteration:
                        return False
                response.genenerate_more_func = generate_more_func
            else:
                response.input_token_count = completion.usage.input_tokens
                response.set_response(completion.content, completion.usage.output_tokens, completion.model_dump())
            
        except Exception as e:
            print(f"Error in Anthropic API call: {str(e)}")
            response.set_response(f"Error: {str(e)}", 0, {"error": str(e)})
        
        return response
    
    def _apply_chat_template(self, chat: List[Dict[str, str]], start_str: str = "") -> str:
        if start_str is not None and len(start_str) > 0:
            raise Exception("Start string not supported by Anthropic")
        return json.dumps(chat)
    
    def _load_model(self):
        self.client = Anthropic(api_key=self.settings.api_key)
    
    def count_tokens(self, text: str) -> int:
        return self.client.count_tokens(text)

    def conversation_to_list(self, conversation: Conversation) -> List[Dict[str,str]]:
        return super().conversation_to_list(conversation, False)