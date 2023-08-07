import sounddevice as sd
import soundfile as sf
import keyboard
import numpy as np
from datetime import datetime


class AudioRecorder:
    def __init__(self, filename, duration=None, sample_rate=44100, channels=2):
        self.filename = filename
        self.duration = duration
        self.sample_rate = sample_rate
        self.channels = channels
        self.stop_recording = False

    def record(self):
        self.recording = sd.InputStream(
            samplerate=self.sample_rate, channels=self.channels
        )
        self.recording.start()
        data = []
        silent_data = []
        silent_seconds = 10
        filename = None
        keyboard.add_hotkey(
            "q", self.set_stop_recording
        )  # Bind 'q' key to stop the recording
        while True:
            frames, _ = self.recording.read(self.sample_rate)
            data.append(frames)
            # Check if the audio volume is below a threshold for 10s
            if np.mean(np.abs(frames)) < 0.001:  # This value might need adjusting
                silent_data.append(frames)
                if len(silent_data) * len(frames) >= self.sample_rate * silent_seconds:
                    # Here we have 10 seconds of silence
                    # Write current data to file
                    filename = self.write_to_file(data)
                    # Clear data and silent_data
                    data = []
                    silent_data = []
            else:
                # If the audio volume is above the threshold, append the silent_data back to data
                data.extend(silent_data)
                silent_data = []
            if self.stop_recording:
                break
        # Process the remaining data if there is any
        if data:
            filename = self.write_to_file(data)
        self.recording.stop()
        keyboard.clear_hotkey("q")  # Clear the hotkey
        return filename

    def write_to_file(self, data):
        data = np.concatenate(data)
        filename = f"{self.filename}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav"
        sf.write(filename, data, self.sample_rate)
        return filename

    def set_stop_recording(self):
        self.stop_recording = True
