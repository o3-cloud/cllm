#!/usr/bin/env python3
"""
Spike to test LiteLLM streaming implementation (ADR-0010)

This spike tests the verified fix using acompletion() with asyncio.run()
to handle streaming responses correctly.
"""

import asyncio
from litellm import acompletion, stream_chunk_builder


async def test_async_streaming(model: str, prompt: str):
    """Test streaming using async approach (verified working)"""
    print(f"Testing async streaming with {model}...")
    print("-" * 60)

    messages = [{"role": "user", "content": prompt}]

    response = await acompletion(
        model=model,
        messages=messages,
        stream=True,
        max_tokens=100  # Keep it short for testing
    )

    chunks = []
    async for chunk in response:
        chunks.append(chunk)
        content = chunk.get('choices', [{}])[0].get('delta', {}).get('content') or ''
        if content:
            print(content, end='', flush=True)

    print("\n" + "-" * 60)

    # Build complete response
    complete_response = stream_chunk_builder(chunks, messages=messages)

    return complete_response


def test_sync_streaming_wrapper(model: str, prompt: str):
    """
    Synchronous wrapper for async streaming.
    This is what we'll integrate into client.complete() for stream=True
    """
    async def _async_stream():
        messages = [{"role": "user", "content": prompt}]
        response = await acompletion(model=model, messages=messages, stream=True, max_tokens=100)
        chunks = []
        async for chunk in response:
            chunks.append(chunk)
            content = chunk.get('choices', [{}])[0].get('delta', {}).get('content') or ''
            if content:
                print(content, end='', flush=True)
        print()  # Final newline
        return stream_chunk_builder(chunks, messages=messages)

    return asyncio.run(_async_stream())


if __name__ == "__main__":
    import sys

    # Default to gpt-3.5-turbo if no model specified
    model = sys.argv[1] if len(sys.argv) > 1 else "gpt-3.5-turbo"
    prompt = "Count from 1 to 5, with a brief explanation for each number."

    print("=" * 60)
    print("STREAMING SPIKE TEST (ADR-0010)")
    print("=" * 60)
    print()

    # Test 1: Direct async streaming
    print("TEST 1: Direct async streaming")
    try:
        result = asyncio.run(test_async_streaming(model, prompt))
        print(f"\nComplete response type: {type(result)}")
        print(f"Response has choices: {hasattr(result, 'choices')}")
        if hasattr(result, 'choices'):
            print(f"Content: {result.choices[0].message.content[:100]}...")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)

    # Test 2: Sync wrapper (what we'll actually use in client.py)
    print("TEST 2: Synchronous wrapper (proposed client.complete implementation)")
    print("-" * 60)
    try:
        result = test_sync_streaming_wrapper(model, prompt)
        print(f"\nComplete response type: {type(result)}")
        print(f"Response has choices: {hasattr(result, 'choices')}")
        if hasattr(result, 'choices'):
            print(f"Content: {result.choices[0].message.content[:100]}...")
        print("\n✅ SUCCESS: Streaming works with async wrapper!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("SPIKE COMPLETE")
    print("=" * 60)
