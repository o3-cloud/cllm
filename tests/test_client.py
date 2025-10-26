"""
Tests for the LLMClient.

These tests verify that the LiteLLM integration works correctly
as specified in ADR-0002.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from cllm import LLMClient


class TestLLMClient:
    """Test suite for LLMClient."""

    def test_client_initialization(self):
        """Test that client initializes correctly."""
        client = LLMClient()
        assert client is not None

    def test_client_initialization_with_api_keys(self):
        """Test that client accepts API keys."""
        api_keys = {
            "OPENAI_API_KEY": "test-key-123",
            "ANTHROPIC_API_KEY": "test-key-456"
        }
        client = LLMClient(api_keys=api_keys)
        assert client is not None

    @patch('cllm.client.completion')
    def test_complete_with_string_message(self, mock_completion):
        """Test completion with a simple string message."""
        # Mock response
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Paris'
                }
            }]
        }
        mock_completion.return_value = mock_response

        client = LLMClient()
        response = client.complete(
            model="gpt-4",
            messages="What is the capital of France?"
        )

        # Verify the completion was called with correct parameters
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args[1]
        assert call_args['model'] == 'gpt-4'
        assert call_args['messages'] == [
            {"role": "user", "content": "What is the capital of France?"}
        ]
        assert call_args['stream'] is False

        # Verify response
        assert response == 'Paris'

    @patch('cllm.client.completion')
    def test_complete_with_message_list(self, mock_completion):
        """Test completion with a list of messages."""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'I can help you!'
                }
            }]
        }
        mock_completion.return_value = mock_response

        client = LLMClient()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "Can you help me?"}
        ]
        response = client.complete(model="gpt-4", messages=messages)

        # Verify messages were passed correctly
        call_args = mock_completion.call_args[1]
        assert call_args['messages'] == messages
        assert response == 'I can help you!'

    @patch('cllm.client.completion')
    def test_complete_with_temperature(self, mock_completion):
        """Test that temperature parameter is passed correctly."""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Creative response'
                }
            }]
        }
        mock_completion.return_value = mock_response

        client = LLMClient()
        response = client.complete(
            model="gpt-4",
            messages="Be creative",
            temperature=1.5
        )

        call_args = mock_completion.call_args[1]
        assert call_args['temperature'] == 1.5

    @patch('cllm.client.completion')
    def test_complete_with_max_tokens(self, mock_completion):
        """Test that max_tokens parameter is passed correctly."""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Short response'
                }
            }]
        }
        mock_completion.return_value = mock_response

        client = LLMClient()
        response = client.complete(
            model="gpt-4",
            messages="Be brief",
            max_tokens=50
        )

        call_args = mock_completion.call_args[1]
        assert call_args['max_tokens'] == 50

    @patch('cllm.client.completion')
    def test_streaming_response(self, mock_completion):
        """Test streaming completion."""
        # Mock streaming chunks
        mock_chunks = [
            {'choices': [{'delta': {'content': 'Hello'}}]},
            {'choices': [{'delta': {'content': ' world'}}]},
            {'choices': [{'delta': {'content': '!'}}]},
        ]
        mock_completion.return_value = iter(mock_chunks)

        client = LLMClient()
        chunks = list(client.complete(
            model="gpt-4",
            messages="Say hello",
            stream=True
        ))

        # Verify streaming was enabled
        call_args = mock_completion.call_args[1]
        assert call_args['stream'] is True

        # Verify chunks
        assert chunks == ['Hello', ' world', '!']

    @patch('cllm.client.completion')
    def test_raw_response(self, mock_completion):
        """Test getting raw response object."""
        mock_response = {
            'id': 'chatcmpl-123',
            'object': 'chat.completion',
            'created': 1677652288,
            'model': 'gpt-4',
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': 'Paris'
                },
                'finish_reason': 'stop',
                'index': 0
            }],
            'usage': {
                'prompt_tokens': 10,
                'completion_tokens': 5,
                'total_tokens': 15
            }
        }
        mock_completion.return_value = mock_response

        client = LLMClient()
        response = client.complete(
            model="gpt-4",
            messages="What is the capital of France?",
            raw_response=True
        )

        # Verify we get the full response object
        assert response == mock_response
        assert 'usage' in response
        assert response['usage']['total_tokens'] == 15

    @patch('cllm.client.completion')
    def test_chat_method(self, mock_completion):
        """Test the chat convenience method."""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Response to conversation'
                }
            }]
        }
        mock_completion.return_value = mock_response

        client = LLMClient()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"}
        ]
        response = client.chat(model="gpt-4", messages=messages)

        assert response == 'Response to conversation'
        call_args = mock_completion.call_args[1]
        assert call_args['messages'] == messages

    @patch('cllm.client.completion')
    def test_multiple_providers_same_interface(self, mock_completion):
        """
        Test that multiple providers can be used with the same interface.
        This is the core benefit of ADR-0002.
        """
        mock_response = {
            'choices': [{
                'message': {
                    'content': '42'
                }
            }]
        }
        mock_completion.return_value = mock_response

        client = LLMClient()
        prompt = "What is 6 * 7?"

        # Test with multiple providers using identical code
        providers = [
            "gpt-4",
            "claude-3-opus-20240229",
            "gemini-pro"
        ]

        for model in providers:
            response = client.complete(model=model, messages=prompt)
            assert response == '42'

        # Verify completion was called 3 times
        assert mock_completion.call_count == 3


class TestAsyncClient:
    """Test suite for async operations."""

    @pytest.mark.asyncio
    @patch('cllm.client.acompletion')
    async def test_async_complete(self, mock_acompletion):
        """Test async completion."""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Async response'
                }
            }]
        }
        mock_acompletion.return_value = mock_response

        client = LLMClient()
        response = await client.acomplete(
            model="gpt-4",
            messages="Test async"
        )

        assert response == 'Async response'
        mock_acompletion.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
