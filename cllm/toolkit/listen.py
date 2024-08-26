import argparse
import tempfile
import queue
import sys
import numpy as np
import sounddevice as sd
import soundfile as sf
from cllm.constants import *

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

class AudioRecorder:
    def __init__(self, args):
        self.args = args
        self.q = queue.Queue()
        self.recording_started = False
        self.below_threshold_start_time = None
        self.finished_recording = False

    def callback(self, indata, frames, time, status):
        """Callback function for audio input stream."""
        if status:
            print(status, file=sys.stderr)
        volume_norm = np.linalg.norm(indata)
        current_time = time.inputBufferAdcTime

        if self.should_start_recording(volume_norm):
            self.start_recording(current_time)

        if self.recording_started:
            self.q.put(indata.copy())

        if self.should_stop_recording(volume_norm, current_time):
            self.stop_recording()

    def should_start_recording(self, volume_norm):
        """Check if recording should start based on volume threshold."""
        return volume_norm >= self.args.threshold and not self.recording_started

    def start_recording(self, current_time):
        """Start the recording process."""
        self.recording_started = True
        self.below_threshold_start_time = current_time

    def should_stop_recording(self, volume_norm, current_time):
        """Check if recording should stop based on volume threshold and duration."""
        return (self.recording_started and volume_norm <= self.args.threshold and
                current_time - self.below_threshold_start_time >= self.args.stop_threshold_duration)

    def stop_recording(self):
        """Stop the recording process."""
        self.recording_started = False
        self.finished_recording = True
        raise sd.CallbackStop()

    def start(self):
        """Start the audio recording process."""
        try:
            self.setup_audio_file()
            self.record_audio()
        except (Exception, KeyboardInterrupt, sd.CallbackStop) as e:
            self.handle_recording_exception(e)

    def setup_audio_file(self):
        """Setup the audio file for recording."""
        if self.args.samplerate is None:
            device_info = sd.query_devices(self.args.device, 'input')
            self.args.samplerate = int(device_info['default_samplerate'])
        if self.args.filename is None:
            if not os.path.exists(self.args.temp_dir):
                os.makedirs(self.args.temp_dir)
            self.args.filename = tempfile.mktemp(prefix=f"{self.args.temp_prefix}_", suffix='.wav', dir=self.args.temp_dir)

    def record_audio(self):
        """Record audio until finished."""
        with sf.SoundFile(self.args.filename, mode='x', samplerate=self.args.samplerate,
                          channels=self.args.channels, subtype=self.args.subtype) as file:
            with sd.InputStream(samplerate=self.args.samplerate, device=self.args.device,
                                channels=self.args.channels, callback=self.callback):
                while not self.finished_recording:
                    file.write(self.q.get())
                print(f"{self.args.filename}")


    def handle_recording_exception(self, e):
        """Handle exceptions during recording."""
        print(f"An error occurred during recording: {e}")
        print(f"{self.args.filename}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-l', '--list-devices', action='store_true', help='show list of audio devices and exit')
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)

    parser = argparse.ArgumentParser(description="Audio Recorder", parents=[parser])
    parser.add_argument('filename', nargs='?', metavar='FILENAME', help='audio file to store recording to')
    parser.add_argument('-d', '--device', type=int_or_str, help='input device (numeric ID or substring)')
    parser.add_argument('-r', '--samplerate', type=int, help='sampling rate')
    parser.add_argument('-c', '--channels', type=int, default=1, help='number of input channels')
    parser.add_argument('-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
    parser.add_argument('--threshold', type=float, default=0.7, help='volume threshold to start recording')
    parser.add_argument('--stop-threshold-duration', type=float, default=2.0, help='duration in seconds the volume must be below threshold to stop recording')
    parser.add_argument('--temp-dir', type=str, default=f"{CLLM_DIR}/recordings", help='directory for temporary files')
    parser.add_argument('--temp-prefix', type=str, default='voice_chat', help='prefix for temporary files')
    return parser.parse_args(remaining)

def main():
    """Main function to run the audio recorder."""
    args = parse_arguments()
    recorder = AudioRecorder(args)
    recorder.start()

if __name__ == "__main__":
    main()