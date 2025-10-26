#!/usr/bin/env python3
"""
Async usage example for CLLM.

This example demonstrates how to use async/await for concurrent LLM calls
to multiple providers.
"""

import asyncio

from cllm import LLMClient


async def query_provider(
    client: LLMClient, model: str, prompt: str, provider_name: str
):
    """Query a single provider asynchronously."""
    try:
        print(f"\n[{provider_name}] Sending request...")
        response = await client.acomplete(model=model, messages=prompt)
        print(f"[{provider_name}] Response: {response}")
        return provider_name, response
    except Exception as e:
        print(f"[{provider_name}] Error: {e}")
        return provider_name, None


async def main():
    client = LLMClient()

    print("=" * 60)
    print("CLLM - Async Multi-Provider Example")
    print("=" * 60)

    # Run queries to multiple providers concurrently
    prompt = "What is 25 * 4? Answer with just the number."

    tasks = [
        query_provider(client, "gpt-4", prompt, "OpenAI"),
        query_provider(client, "claude-3-opus-20240229", prompt, "Anthropic"),
        query_provider(client, "gemini-pro", prompt, "Google"),
    ]

    print("\nRunning concurrent queries to multiple providers...")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    for provider, response in results:
        if isinstance(response, Exception):
            print(f"{provider}: Error - {response}")
        elif response:
            print(f"{provider}: {response}")
        else:
            print(f"{provider}: No response")


if __name__ == "__main__":
    asyncio.run(main())
