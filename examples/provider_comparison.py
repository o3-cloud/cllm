#!/usr/bin/env python3
"""
Provider comparison example.

This example demonstrates how easy it is to switch between providers
and compare their responses to the same prompt.
"""

from cllm import LLMClient
import time


def compare_providers(client: LLMClient, prompt: str, models: dict):
    """
    Compare responses from different providers.

    Args:
        client: LLMClient instance
        prompt: The prompt to send to all providers
        models: Dict of {provider_name: model_name}
    """
    print(f"\nPrompt: {prompt}")
    print("=" * 80)

    results = {}

    for provider_name, model_name in models.items():
        print(f"\n[{provider_name}]")
        print("-" * 80)
        try:
            start_time = time.time()
            response = client.complete(
                model=model_name,
                messages=prompt,
                max_tokens=100
            )
            elapsed_time = time.time() - start_time

            print(f"Response: {response}")
            print(f"Time: {elapsed_time:.2f}s")
            results[provider_name] = {
                "response": response,
                "time": elapsed_time,
                "error": None
            }
        except Exception as e:
            print(f"Error: {e}")
            results[provider_name] = {
                "response": None,
                "time": 0,
                "error": str(e)
            }

    return results


def main():
    client = LLMClient()

    print("=" * 80)
    print("CLLM - Provider Comparison Example")
    print("=" * 80)
    print("\nThis demonstrates the key benefit of LiteLLM: same code, different providers!")

    # Define providers to compare
    # Note: Only providers with valid API keys will work
    models = {
        "OpenAI GPT-4": "gpt-4",
        "OpenAI GPT-3.5": "gpt-3.5-turbo",
        "Anthropic Claude 3 Opus": "claude-3-opus-20240229",
        "Anthropic Claude 3 Sonnet": "claude-3-sonnet-20240229",
        "Google Gemini Pro": "gemini-pro",
    }

    # Test with a simple question
    results = compare_providers(
        client,
        "Explain what an API is in one sentence.",
        models
    )

    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)

    successful = [p for p, r in results.items() if r["error"] is None]
    failed = [p for p, r in results.items() if r["error"] is not None]

    print(f"\nSuccessful providers: {len(successful)}/{len(models)}")
    if successful:
        print("  - " + "\n  - ".join(successful))

    if failed:
        print(f"\nFailed providers: {len(failed)}/{len(models)}")
        print("  (These likely need API keys configured)")
        print("  - " + "\n  - ".join(failed))

    print("\n" + "=" * 80)
    print("Key Takeaway:")
    print("  The same client.complete() call works across ALL providers!")
    print("  Just change the model name to switch providers.")
    print("=" * 80)


if __name__ == "__main__":
    main()
