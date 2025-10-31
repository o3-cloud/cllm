"""
Tests for the LLMClient.

These tests verify that the LiteLLM integration works correctly
as specified in ADR-0002.
"""

from unittest.mock import patch

import pytest

from cllm import LLMClient


class TestLLMClient:
    """Test suite for LLMClient."""

    @patch("cllm.client.completion")
    def test_complete_with_string_message(self, mock_completion):
        """Test completion with a simple string message."""
        # Mock response
        mock_response = {"choices": [{"message": {"content": "Paris"}}]}
        mock_completion.return_value = mock_response

        client = LLMClient()
        response = client.complete(
            model="gpt-4", messages="What is the capital of France?"
        )

        # Verify the completion was called with correct parameters
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args[1]
        assert call_args["model"] == "gpt-4"
        assert call_args["messages"] == [
            {"role": "user", "content": "What is the capital of France?"}
        ]
        assert call_args["stream"] is False

        # Verify response
        assert response == "Paris"

    @patch("cllm.client.completion")
    def test_complete_with_message_list(self, mock_completion):
        """Test completion with a list of messages."""
        mock_response = {"choices": [{"message": {"content": "I can help you!"}}]}
        mock_completion.return_value = mock_response

        client = LLMClient()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "Can you help me?"},
        ]
        response = client.complete(model="gpt-4", messages=messages)

        # Verify messages were passed correctly
        call_args = mock_completion.call_args[1]
        assert call_args["messages"] == messages
        assert response == "I can help you!"

    @patch("cllm.client.completion")
    def test_complete_with_temperature(self, mock_completion):
        """Test that temperature parameter is passed correctly."""
        mock_response = {"choices": [{"message": {"content": "Creative response"}}]}
        mock_completion.return_value = mock_response

        client = LLMClient()
        client.complete(model="gpt-4", messages="Be creative", temperature=1.5)

        call_args = mock_completion.call_args[1]
        assert call_args["temperature"] == 1.5

    @patch("cllm.client.stream_chunk_builder")
    @patch("cllm.client.acompletion")
    def test_streaming_response(self, mock_acompletion, mock_stream_chunk_builder):
        """Test streaming completion with async wrapper (ADR-0010)."""

        # Mock streaming chunks
        async def mock_async_gen():
            chunks = [
                {"choices": [{"delta": {"content": "Hello"}}]},
                {"choices": [{"delta": {"content": " world"}}]},
                {"choices": [{"delta": {"content": "!"}}]},
            ]
            for chunk in chunks:
                yield chunk

        mock_acompletion.return_value = mock_async_gen()

        # Mock stream_chunk_builder to return a proper response object
        class MockResponse:
            def __init__(self):
                self.choices = [
                    type(
                        "obj",
                        (object,),
                        {
                            "message": type(
                                "obj", (object,), {"content": "Hello world!"}
                            )()
                        },
                    )()
                ]

        mock_stream_chunk_builder.return_value = MockResponse()

        client = LLMClient()
        response = client.complete(model="gpt-4", messages="Say hello", stream=True)

        # Verify acompletion was called with streaming enabled
        call_args = mock_acompletion.call_args[1]
        assert call_args["stream"] is True

        # Verify response is the complete string (not chunks)
        assert response == "Hello world!"

        # Verify stream_chunk_builder was called
        mock_stream_chunk_builder.assert_called_once()

    @patch("cllm.client.completion")
    def test_raw_response(self, mock_completion):
        """Test getting raw response object."""
        mock_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Paris"},
                    "finish_reason": "stop",
                    "index": 0,
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        mock_completion.return_value = mock_response

        client = LLMClient()
        response = client.complete(
            model="gpt-4", messages="What is the capital of France?", raw_response=True
        )

        # Verify we get the full response object
        assert response == mock_response
        assert "usage" in response
        assert response["usage"]["total_tokens"] == 15

    @patch("cllm.client.completion")
    def test_chat_method(self, mock_completion):
        """Test the chat convenience method."""
        mock_response = {
            "choices": [{"message": {"content": "Response to conversation"}}]
        }
        mock_completion.return_value = mock_response

        client = LLMClient()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"},
        ]
        response = client.chat(model="gpt-4", messages=messages)

        assert response == "Response to conversation"
        call_args = mock_completion.call_args[1]
        assert call_args["messages"] == messages


class TestAsyncClient:
    """Test suite for async operations."""

    @pytest.mark.asyncio
    @patch("cllm.client.acompletion")
    async def test_async_complete(self, mock_acompletion):
        """Test async completion."""
        mock_response = {"choices": [{"message": {"content": "Async response"}}]}
        mock_acompletion.return_value = mock_response

        client = LLMClient()
        response = await client.acomplete(model="gpt-4", messages="Test async")

        assert response == "Async response"
        mock_acompletion.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
