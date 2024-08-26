import argparse
from litellm import transcription
from cllm.constants import *

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Speech to Text CLI tool using LiteLLM")
    parser.add_argument("-f", "--audio_file", required=True, default="", help="Path to the audio file for transcription")
    parser.add_argument("-m", "--model", default="whisper-1", help="Model to use for transcription (default: whisper-1)")
    return parser.parse_args()

def transcribe_audio(audio_file_path, model):
    """Transcribe the audio file using the specified model."""
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = transcription(model=model, file=audio_file)
            return response.text
    except FileNotFoundError:
        return f"Error: Audio file not found: {audio_file_path}"
    except Exception as e:
        return f"Error during transcription: {str(e)}"

def main():
    """Main function to run the transcription process."""
    args = parse_arguments()
    transcription_result = transcribe_audio(args.audio_file, args.model)
    print(transcription_result)

if __name__ == "__main__":
    main()