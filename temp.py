import requests
from typing import List, Dict, Any, Optional, Sequence, Union
from pydantic import Field
from langchain.schema import BaseChatModel, ChatResult, AIMessage, ChatGeneration, BaseMessage
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.tools import BaseTool

class CustomEndpointLLM(BaseChatModel):
    """Custom Chat Model that makes requests to an endpoint.
    Args:
        endpoint_url (str): The URL of the LLM endpoint
        model (str): Model identifier to use
        temperature (float, optional): Sampling temperature. Defaults to 0.7
        max_tokens (int, optional): Maximum number of tokens to generate. Defaults to 256
        top_p (float, optional): Nucleus sampling parameter. Defaults to 1.0
    """
    endpoint_url: str = Field(..., description="URL of the LLM endpoint")
    model: str = Field(..., description="Model identifier to use")
    temperature: float = Field(0.7, description="Sampling temperature")
    max_tokens: int = Field(2000, description="Maximum number of tokens to generate")
    top_p: float = Field(1.0, description="Nucleus sampling parameter")

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat response.
        Args:
            messages: List of messages in the conversation
            stop: Stop sequences (not implemented)
            run_manager: Callback manager
            **kwargs: Additional arguments to pass to the endpoint
        """
        if stop is not None:
            raise ValueError("Stop sequences are not supported")
        # Convert messages to a prompt string
        prompt = "\n".join([msg.content for msg in messages])
        # Prepare the request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        try:
            # Request to the endpoint
            response = requests.post(self.endpoint_url, json=payload)
            response.raise_for_status()
            # Parse the response
            result = response.json()["choices"][0]
            # Extract the generated text - adjust the key based on your API response structure
            # Assuming the response has a structure like {"text": "generated text"}
            if "text" in result:
                generated_text = result["text"].strip()
            else:
                raise ValueError(f"Unexpected response format: {result}")
            # Create a ChatGeneration object
            message = AIMessage(content=generated_text)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error making request to endpoint: {str(e)}")

    def bind_tools(
        self, tools: Sequence[BaseTool], tool_choice: Optional[Union[str, Dict]] = None
    ) -> BaseChatModel:
        """Bind tools to the model.
        
        Args:
            tools: The tools to bind to the model
            tool_choice: The tool choice configuration, if any
            
        Returns:
            The model with bound tools
        """
        # Since the endpoint doesn't directly support tools, we'll create a wrapper
        # that injects tool descriptions into the prompt
        
        class CustomEndpointLLMWithTools(CustomEndpointLLM):
            _tools = list(tools)
            _tool_choice = tool_choice
            
            def _generate(
                self,
                messages: List[BaseMessage],
                stop: Optional[List[str]] = None,
                run_manager: Optional[CallbackManagerForLLMRun] = None,
                **kwargs: Any,
            ) -> ChatResult:
                # Create a modified version of the messages that includes tool descriptions
                modified_messages = list(messages)
                
                # Create tool descriptions for the prompt
                tool_descriptions = "\n\nAvailable tools:\n"
                for tool in self._tools:
                    tool_descriptions += f"- {tool.name}: {tool.description}\n"
                
                if tool_choice:
                    tool_choice_info = f"\nPreferred tool to use: {self._tool_choice}\n"
                    tool_descriptions += tool_choice_info
                
                # Add tool instructions to the system message or create a new one
                system_message_found = False
                for i, message in enumerate(modified_messages):
                    if hasattr(message, "type") and message.type == "system":
                        modified_messages[i].content += tool_descriptions
                        system_message_found = True
                        break
                
                if not system_message_found and len(modified_messages) > 0:
                    # Add to the first message
                    modified_messages[0].content = tool_descriptions + "\n" + modified_messages[0].content
                
                # Call the parent _generate method with modified messages
                return super()._generate(modified_messages, stop, run_manager, **kwargs)
        
        # Return a new instance with the same configuration
        return CustomEndpointLLMWithTools(
            endpoint_url=self.endpoint_url,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p
        )
            
    @property
    def llm_type(self) -> str:
        """Return type of LLM."""
        return "custom_endpoint"
    
    @property
    def identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model,
            "endpoint_url": self.endpoint_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }