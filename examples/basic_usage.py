#!/usr/bin/env python3
"""
Basic usage example for CLLM with multiple providers.

This example demonstrates ADR-0002 implementation: switching between
different LLM providers using the same code interface.
"""

from cllm import LLMClient


def main():
    # Initialize the client
    # API keys are read from environment variables:
    # - OPENAI_API_KEY for OpenAI
    # - ANTHROPIC_API_KEY for Anthropic
    # - GOOGLE_API_KEY for Google/Gemini
    client = LLMClient()

    print("=" * 60)
    print("CLLM - Multi-Provider LLM Client Examples")
    print("=" * 60)

    # Example 1: Simple completion with OpenAI
    print("\n1. OpenAI GPT-4:")
    print("-" * 60)
    try:
        response = client.complete(
            model="gpt-4",
            messages="What is the capital of France? Answer in one word."
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Same code, different provider (Anthropic)
    print("\n2. Anthropic Claude:")
    print("-" * 60)
    try:
        response = client.complete(
            model="claude-3-opus-20240229",
            messages="What is the capital of France? Answer in one word."
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Example 3: Google Gemini
    print("\n3. Google Gemini:")
    print("-" * 60)
    try:
        response = client.complete(
            model="gemini-pro",
            messages="What is the capital of France? Answer in one word."
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Example 4: Multi-turn conversation
    print("\n4. Multi-turn conversation (using configured model):")
    print("-" * 60)
    try:
        conversation = [
            {"role": "user", "content": "Hello! Can you help me?"},
            {"role": "assistant", "content": "Of course! I'd be happy to help. What do you need?"},
            {"role": "user", "content": "What's 2+2?"}
        ]
        response = client.chat(
            model="gpt-4",  # Can switch to any provider
            messages=conversation
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Example 5: Streaming response
    print("\n5. Streaming response:")
    print("-" * 60)
    try:
        print("Response: ", end="", flush=True)
        for chunk in client.complete(
            model="gpt-4",
            messages="Count from 1 to 5.",
            stream=True
        ):
            print(chunk, end="", flush=True)
        print()  # New line after streaming
    except Exception as e:
        print(f"\nError: {e}")

    # Example 6: With temperature parameter
    print("\n6. Creative response (high temperature):")
    print("-" * 60)
    try:
        response = client.complete(
            model="gpt-4",
            messages="Write a one-sentence creative story about a robot.",
            temperature=1.5
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
