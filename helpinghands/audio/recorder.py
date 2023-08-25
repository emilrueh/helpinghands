from ..utility.logger import get_logger

logger = get_logger()

from ..utility.helper import log_exception

import sounddevice as sd
import soundfile as sf
import numpy as np
from datetime import datetime
import os, keyboard

from ..ai import call_whisper
from ..utility.data import write_to_txt_file


class AudioRecorder:
    def __init__(
        self,
        filename,
        output_directory,
        duration=600,  # seconds
        intervals=3,  # seconds
        sample_rate=44100,
        channels=2,
        stop_words: list[str] = None,
        whisper_api_key=None,
        transcript_file_name=None,
        conversation_file_name=None,
        text_file_dir=None,
    ):
        self.filename = filename
        self.output_directory = output_directory
        self.duration = duration
        self.intervals = intervals
        self.sample_rate = sample_rate
        self.channels = channels
        self.stop_recording = False
        self.stop_words = stop_words if isinstance(stop_words, list) else [stop_words]
        self.whisper_api_key = whisper_api_key
        self.transcript_file_name = transcript_file_name
        self.conversation_file_name = conversation_file_name
        self.text_file_dir = text_file_dir
        self.conversation = ""

        self.audio_file = None
        self.transcript_file_path = None

    def record(self, transcribe=False):
        try:
            total_duration = 0
            self.stop_words = [word.casefold() for word in self.stop_words]

            while total_duration < self.duration:
                self.recording = sd.InputStream(
                    samplerate=self.sample_rate, channels=self.channels
                )
                self.recording.start()
                start_time = datetime.now()
                data = []
                keyboard.add_hotkey("q", self.set_stop_recording)

                # Preallocate array for performance increase
                data_array_size = (self.sample_rate * self.intervals, self.channels)
                data = np.empty(data_array_size, dtype=np.float32)
                index = 0

                segment_duration = 0
                transcript = ""
                logger.debug(f'Recording started at {start_time.strftime("%H:%M:%S")}')
                while True:
                    frames, _ = self.recording.read(self.sample_rate)
                    data[index : index + len(frames)] = frames
                    index += len(frames)
                    segment_duration = (datetime.now() - start_time).seconds

                    if segment_duration >= self.intervals:
                        self.audio_file = self.write_to_wav_file(data[:index])
                        index = 0  # Reset index
                        data = np.empty(data_array_size, dtype=np.float32)  # Reset data
                        if transcribe:
                            transcript = self.voice_transcript(self.audio_file)
                            self.conversation += f" {transcript}"
                            self.check_stop_words(transcript)
                            self.transcript_file_path = os.path.join(
                                self.text_file_dir, f"{self.transcript_file_name}.txt"
                            )

                    if self.stop_recording:
                        break

                self.recording.stop()
                logger.debug(
                    f'Recording stopped at {datetime.now().strftime("%H:%M:%S")}'
                )
                keyboard.clear_hotkey("q")
                self.stop_recording = False  # Reset for the next segment

            if transcribe:
                write_to_txt_file(
                    self.conversation,
                    file_name=self.conversation_file_name,
                    output_directory=self.text_file_dir,
                    mode="write",
                )

            # deleting 3s files
            transcript_file_path = (
                os.path.join(self.text_file_dir, f"{self.transcript_file_name}.txt")
                if transcribe
                else None
            )

            if transcribe:
                return self.conversation
            else:
                return self.audio_file
        except Exception as e:
            log_exception(e)
        finally:
            self.cleanup_files()

    def write_to_wav_file(self, data):
        filename = os.path.join(
            self.output_directory,
            f"{self.filename}.wav",
        )
        sf.write(filename, data, self.sample_rate)
        return filename

    def set_stop_recording(self):
        self.stop_recording = True

    def check_stop_words(self, text: str):
        if any(stop_word in text for stop_word in self.stop_words):
            self.set_stop_recording()

    def voice_transcript(self, output_audio_file):
        transcript = call_whisper(self.whisper_api_key, output_audio_file)

        write_to_txt_file(
            transcript,
            file_name=self.transcript_file_name,
            output_directory=self.text_file_dir,
            mode="write",
        )
        print(transcript, end=" ", flush=True)
        return transcript

    def cleanup_files(self):
        if self.audio_file:
            logger.debug(f"Attempting to delete {self.audio_file}")
            os.remove(self.audio_file)
        if self.transcript_file_path:
            logger.debug(f"Attempting to delete {self.transcript_file_path}")
            os.remove(self.transcript_file_path)
