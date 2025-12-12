import ollama
from typing import List, Generator, Dict, Any

class OllamaService:
    """
    Service layer to handle interactions with the Ollama API.
    Acts as a Facade to the underlying ollama library.
    """

    def get_models(self) -> List[str]:
        """
        Fetches the list of available local models.
        
        Returns:
            List[str]: A list of model names.
        """
        try:
            models_response = ollama.list()
            
            # The ollama library returns a ListResponse object where 'models' is an attribute,
            # and each model in that list is an object with a 'model' attribute (not 'name').
            if hasattr(models_response, 'models'):
                 return [model.model for model in models_response.models]
            
            # Fallback for dictionary-like responses (older versions or different environments)
            if isinstance(models_response, dict) and 'models' in models_response:
                 return [model['name'] if 'name' in model else model['model'] for model in models_response['models']]
            
            return []
        except Exception as e:
            # Log the error or re-raise a custom exception if needed
            print(f"Error fetching models: {e}")
            return []

    def chat_stream(self, model: str, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        Generates a streaming response from the Ollama chat API.

        Args:
            model (str): The name of the model to use.
            messages (List[Dict[str, str]]): The chat history messages.

        Yields:
            str: Chunks of the response content.
        
        Raises:
            Exception: If the API call fails.
        """
        try:
            for response in ollama.chat(model=model, messages=messages, stream=True):
                # The response chunk is also an object in newer library versions
                content = ""
                
                # Check for object attribute access first (newer library)
                if hasattr(response, 'message') and hasattr(response.message, 'content'):
                    content = response.message.content
                # Fallback to dictionary access
                elif isinstance(response, dict) and 'message' in response and 'content' in response['message']:
                    content = response['message']['content']
                
                if content:
                    yield content
        except Exception as e:
            raise Exception(f"Error during chat generation: {e}")
