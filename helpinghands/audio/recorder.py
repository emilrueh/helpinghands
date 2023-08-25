from ..utility.logger import get_logger

logger = get_logger()

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

    def record(self, transcribe=False):
        total_duration = 0
        self.stop_words = [word.casefold() for word in self.stop_words]

        while total_duration < self.duration:
            self.recording = sd.InputStream(
                samplerate=self.sample_rate, channels=self.channels
            )
            self.recording.start()
            start_time = datetime.now()
            data = []
            filename = None
            keyboard.add_hotkey("q", self.set_stop_recording)

            segment_duration = 0
            transcript = ""
            logger.debug(f'Recording started at {start_time.strftime("%H:%M:%S")}')
            while True:
                frames, _ = self.recording.read(self.sample_rate)
                data.append(frames)
                segment_duration = (datetime.now() - start_time).seconds

                if segment_duration >= self.intervals:  # Check for 3-second intervals
                    filename = self.write_to_wav_file(data)
                    if transcribe:
                        transcript = self.voice_transcript(
                            filename
                        )  # Transcribe the audio
                        self.conversation += f" {transcript}"
                        self.check_stop_words(transcript)
                    data = []

                    total_duration += segment_duration  # Increment total_duration
                    start_time = datetime.now()  # Reset start_time for next interval

                if self.stop_recording:
                    break

            self.recording.stop()
            logger.debug(f'Recording stopped at {datetime.now().strftime("%H:%M:%S")}')
            keyboard.clear_hotkey("q")
            self.stop_recording = False  # Reset for the next segment

        audio_file = filename

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
        self.cleanup_files(audio_file, transcript_file_path)

        if transcribe:
            return self.conversation, audio_file
        else:
            return audio_file

    def write_to_wav_file(self, data):
        data = np.concatenate(data)
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

    def cleanup_files(self, audio_file, transcript_file=None):
        os.remove(audio_file)
        if transcript_file:
            os.remove(transcript_file)
