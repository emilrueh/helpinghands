import sounddevice as sd
import numpy as np
import threading, wavio
import os


class AudioRecorder:
    def __init__(
        self,
        sample_rate=44100,
        channels=2,
        audio_dir=".",
        audio_file_name="output",
        stop_button="q",
        max_rec_time=None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_dir = audio_dir
        self.audio_file_name = audio_file_name
        self.audio_file_path = os.path.join(self.audio_dir, f"{self.audio_file_name}.wav")
        self.stop_button = stop_button
        self.max_rec_time = max_rec_time
        self.stop_event = threading.Event()

    def record(self):
        audio_data = []

        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels) as stream:
            stop_thread = threading.Thread(target=self.listen_for_stop)
            timer_thread = threading.Thread(target=self.time_limit) if self.max_rec_time else None

            stop_thread.start()
            if timer_thread:
                timer_thread.start()

            while not self.stop_event.is_set():
                data, _ = stream.read(1000)
                audio_data.append(data)

            stop_thread.join()
            if timer_thread:
                timer_thread.join()

        audio_data = np.vstack(audio_data)
        audio_data = (audio_data * 32767).astype(np.int16)

        wavio.write(self.audio_file_path, audio_data, self.sample_rate, sampwidth=2)

        return self.audio_file_path

    def listen_for_stop(self):
        while not self.stop_event.is_set():
            inp = input()
            if inp == self.stop_button:
                self.stop_event.set()
                break

    def time_limit(self):
        self.stop_event.wait(timeout=self.max_rec_time)
        self.stop_event.set()
