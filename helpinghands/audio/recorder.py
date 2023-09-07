import sounddevice as sd
import numpy as np
import wavio
import os
import threading


class AudioRecorder:
    def __init__(self, sample_rate=44100, channels=2, audio_dir=".", audio_file_name="output", stop_button="q"):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_dir = audio_dir
        self.audio_file_name = audio_file_name
        self.audio_file_path = os.path.join(self.audio_dir, f"{self.audio_file_name}.wav")
        self.stop_button = stop_button
        self.is_recording = False

    def record(self):
        audio_data = []

        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels) as stream:
            self.is_recording = True
            stop_thread = threading.Thread(target=self.listen_for_stop)
            stop_thread.start()

            while self.is_recording:
                data, _ = stream.read(1000)
                audio_data.append(data)

            stop_thread.join()

        # converting to 16bit int
        audio_data = np.vstack(audio_data)
        audio_data = (audio_data * 32767).astype(np.int16)  # Scale float data to 16-bit PCM format

        wavio.write(
            self.audio_file_path, audio_data, self.sample_rate, sampwidth=2
        )  # Specify sampwidth as 2 for 16-bit

        return self.audio_file_path

    def listen_for_stop(self):
        while True:
            inp = input()
            if inp == self.stop_button:
                self.is_recording = False
                break
