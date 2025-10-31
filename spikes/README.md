# Spikes Directory

This directory contains isolated spike implementations for testing and validating new features before integrating them into the main codebase.

## Streaming Spike (ADR-0010)

**File:** `streaming_spike.py`

Tests the LiteLLM streaming implementation using the async/await approach verified in ADR-0010.

### Usage

```bash
# Test with default model (gpt-3.5-turbo)
uv run python spikes/streaming_spike.py

# Test with specific model
uv run python spikes/streaming_spike.py gpt-4
uv run python spikes/streaming_spike.py claude-3-5-sonnet-20241022
```

### Expected Behavior

- Real-time streaming output should appear character by character
- Complete response object should be returned after streaming completes
- Both the direct async and sync wrapper approaches should work

### What This Validates

1. LiteLLM's `acompletion()` with `stream=True` returns an async generator
2. Chunks can be collected while displaying content in real-time
3. `stream_chunk_builder()` successfully reconstructs the complete response
4. The sync wrapper using `asyncio.run()` works for integration into `client.complete()`

### Next Steps

If this spike succeeds:

1. Integrate the sync wrapper pattern into `src/cllm/client.py`
2. Update `src/cllm/cli.py` if needed (should already pass stream flag)
3. Add proper unit tests with mocked async generators
4. Update integration tests to verify real API streaming
