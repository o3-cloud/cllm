"""
Core LLM client implementation using LiteLLM.

This module implements ADR-0002: Use LiteLLM for LLM Provider Abstraction.
It provides a unified interface for interacting with 100+ LLM providers
using the OpenAI-compatible API format.
"""

from typing import Any, Dict, List, Optional, Union, Iterator
import os
from litellm import completion, acompletion


class LLMClient:
    """
    Unified LLM client for interacting with multiple providers.

    Uses LiteLLM to provide a consistent interface across OpenAI, Anthropic,
    Google, Cohere, AWS Bedrock, and 100+ other providers.

    Examples:
        >>> client = LLMClient()
        >>> # Using OpenAI
        >>> response = client.complete("gpt-4", "Hello, world!")
        >>> print(response)

        >>> # Using Anthropic (same interface)
        >>> response = client.complete("claude-3-opus-20240229", "Hello, world!")
        >>> print(response)

        >>> # Streaming responses
        >>> for chunk in client.complete("gpt-4", "Tell me a story", stream=True):
        ...     print(chunk, end="", flush=True)
    """

    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize the LLM client.

        Args:
            api_keys: Optional dictionary of provider API keys.
                     If not provided, will use environment variables.
                     Keys should match LiteLLM's conventions:
                     - OPENAI_API_KEY for OpenAI
                     - ANTHROPIC_API_KEY for Anthropic
                     - GOOGLE_API_KEY for Google/Gemini
                     - COHERE_API_KEY for Cohere
                     etc.
        """
        if api_keys:
            for key, value in api_keys.items():
                os.environ[key] = value

    def complete(
        self,
        model: str,
        messages: Union[str, List[Dict[str, str]]],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Union[str, Iterator[str], Dict[str, Any]]:
        """
        Generate a completion using the specified model.

        This is a synchronous wrapper around litellm.completion() that provides
        a simplified interface for common use cases.

        Args:
            model: Model name (e.g., "gpt-4", "claude-3-opus-20240229", "gemini-pro")
            messages: Either a string prompt or a list of message dicts in OpenAI format
                     [{"role": "user", "content": "Hello"}]
            stream: If True, return an iterator of response chunks
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters to pass to litellm.completion()

        Returns:
            If stream=False: The text content of the response (string)
            If stream=True: An iterator yielding response chunks (strings)
            If raw_response=True in kwargs: The raw LiteLLM response object

        Raises:
            Exception: Provider-specific errors (mapped to OpenAI exception types by LiteLLM)
        """
        # Convert string prompt to messages format
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        # Build parameters
        params = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        # Add any additional parameters
        params.update(kwargs)

        # Check if user wants raw response
        raw_response = kwargs.pop("raw_response", False)

        # Make the API call
        response = completion(**params)

        # Handle streaming responses
        if stream:
            return self._stream_response(response)

        # Return raw response if requested
        if raw_response:
            return response

        # Extract and return the text content
        return response['choices'][0]['message']['content']

    async def acomplete(
        self,
        model: str,
        messages: Union[str, List[Dict[str, str]]],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Union[str, Iterator[str], Dict[str, Any]]:
        """
        Async version of complete().

        Args:
            Same as complete()

        Returns:
            Same as complete()
        """
        # Convert string prompt to messages format
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        # Build parameters
        params = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        # Add any additional parameters
        params.update(kwargs)

        # Check if user wants raw response
        raw_response = kwargs.pop("raw_response", False)

        # Make the async API call
        response = await acompletion(**params)

        # Handle streaming responses
        if stream:
            return self._stream_response(response)

        # Return raw response if requested
        if raw_response:
            return response

        # Extract and return the text content
        return response['choices'][0]['message']['content']

    def _stream_response(self, response: Any) -> Iterator[str]:
        """
        Process streaming response and yield text chunks.

        Args:
            response: Streaming response from litellm.completion()

        Yields:
            Text chunks from the streaming response
        """
        for chunk in response:
            if chunk['choices'][0].get('delta', {}).get('content'):
                yield chunk['choices'][0]['delta']['content']

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs: Any
    ) -> str:
        """
        Convenience method for multi-turn chat conversations.

        Args:
            model: Model name
            messages: List of message dicts in OpenAI format
                     [{"role": "user", "content": "Hello"},
                      {"role": "assistant", "content": "Hi!"},
                      {"role": "user", "content": "How are you?"}]
            **kwargs: Additional parameters

        Returns:
            The assistant's response text
        """
        return self.complete(model=model, messages=messages, **kwargs)
