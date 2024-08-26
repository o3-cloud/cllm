# cllm-listen

`cllm-listen` is a command-line interface (CLI) tool designed for recording audio based on volume thresholds. It uses the `sounddevice` and `soundfile` libraries to capture and save audio input to a file. The recording starts when the volume exceeds a specified threshold and stops when the volume remains below the threshold for a certain duration.

## Usage

The CLI tool supports various options to customize the recording process, including specifying the input device, sample rate, number of channels, and volume thresholds.

### Basic Command

To start recording audio, simply run:

```bash
cllm-listen [options]
```

### Options

- `-l, --list-devices`: Show a list of available audio devices and exit.
- `filename`: The name of the audio file to store the recording. If not provided, a temporary file will be created.
- `-d, --device`: Input device (numeric ID or substring).
- `-r, --samplerate`: Sampling rate.
- `-c, --channels`: Number of input channels (default: 1).
- `-t, --subtype`: Sound file subtype (e.g., "PCM_24").
- `--threshold`: Volume threshold to start recording (default: 0.7).
- `--stop-threshold-duration`: Duration in seconds the volume must be below the threshold to stop recording (default: 2.0).
- `--temp-dir`: Directory for temporary files (default: `${CLLM_DIR}/recordings`).
- `--temp-prefix`: Prefix for temporary files (default: `voice_chat`).

### Example

To record audio using the default settings and save it to a file named `output.wav`:

```bash
cllm-listen
```

To list all available audio devices:

```bash
cllm-listen --list-devices
```

To record audio with a specific device and sample rate:

```bash
cllm-listen -d 1 -r 44100 output.wav
```

## Configuration

The tool uses environment variables for configuration. You can set these variables in your environment or in a `.env` file.

- `CLLM_DIR`: Directory where temporary files will be stored. Default is `${HOME}/.cllm`.

## Logging

The tool prints status messages and errors to the standard output and standard error streams. This helps in debugging and understanding the recording process.

## Command Line Arguments

- `-l, --list-devices`: Show a list of audio devices and exit.
- `filename`: The name of the audio file to store the recording. If not provided, a temporary file will be created.
- `-d, --device`: Input device (numeric ID or substring).
- `-r, --samplerate`: Sampling rate.
- `-c, --channels`: Number of input channels (default: 1).
- `-t, --subtype`: Sound file subtype (e.g., "PCM_24").
- `--threshold`: Volume threshold to start recording (default: 0.7).
- `--stop-threshold-duration`: Duration in seconds the volume must be below the threshold to stop recording (default: 2.0).
- `--temp-dir`: Directory for temporary files (default: `${CLLM_DIR}/recordings`).
- `--temp-prefix`: Prefix for temporary files (default: `voice_chat`).

## Error Handling

The tool handles exceptions during the recording process and prints error messages to the standard error stream. This ensures that users are informed of any issues that occur during recording.