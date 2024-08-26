# CLLM Speech to Text CLI Tool

This CLI tool allows you to transcribe audio files to text using the LiteLLM library. It supports specifying the audio file and the transcription model to use.

## Usage

The CLI tool supports transcribing an audio file to text.

### Example

```bash
cllm-speech-text -f path/to/audio/file.wav -m whisper-1
```

## Command Line Arguments

- `-f, --audio_file`: Path to the audio file for transcription (required).
- `-m, --model`: Model to use for transcription (default: `whisper-1`).

## Configuration

The tool uses constants defined in the `cllm.constants` module. Ensure that the `CLLM_DIR` is correctly set in your environment or in the constants module.

## Logging

The tool does not include built-in logging. You can add logging as needed by modifying the script.

## Error Handling

The tool handles the following errors:
- `FileNotFoundError`: If the specified audio file is not found.
- General exceptions during the transcription process, which are caught and reported.

## Example

To transcribe an audio file located at `./recordings/sample.wav` using the default model `whisper-1`, run:

```bash
cllm-speech-text -f ./recordings/sample.wav
```

To specify a different model, for example, `whisper-2`, run:

```bash
cllm-speech-text -f ./recordings/sample.wav -m whisper-2
```