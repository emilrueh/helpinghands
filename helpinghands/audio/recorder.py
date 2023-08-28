from ..utility.logger import get_logger
from ..utility.helper import log_exception

import sounddevice as sd
import soundfile as sf
import queue
import numpy as np
from pydub import AudioSegment
from pydub.silence import detect_silence
from scipy.signal import butter, filtfilt
from collections import deque

from datetime import datetime
import os, keyboard, time

from ..ai import call_whisper
from ..utility.data import write_to_txt_file


import numpy as np
import sounddevice as sd
import os
from datetime import datetime
import keyboard
import soundfile as sf

import tempfile

# Assume that log_exception, write_to_txt_file, and call_whisper are defined elsewhere


class AudioRecorder:
    def __init__(
        self,
        filename,
        output_directory,
        duration=600,
        intervals=3,
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
        self.transcript_file_path = None
        self.conversation_file_name = conversation_file_name
        self.text_file_dir = text_file_dir
        self.conversation = ""
        self.all_audio_data = np.array([], dtype=np.float32).reshape(0, self.channels)
        self.audio_file = None
        self.setup_recording()

    def record(self, transcribe=False):
        try:
            self.start_recording()
            while not self.stop_recording:
                self._record_segment(transcribe)
            self.final_output(transcribe)

        except KeyboardInterrupt:
            self.write_to_wav_file(self.all_audio_data, filename=f"full_{self.filename}")
            if transcribe:
                write_to_txt_file(
                    self.conversation,
                    file_name=self.conversation_file_name,
                    output_directory=self.text_file_dir,
                    mode="write",
                )
        except Exception as e:
            log_exception(e)
        finally:
            self.cleanup()

    def setup_recording(self):
        self.stop_words = [word.casefold() for word in self.stop_words]
        ringbuffer_size = int(self.sample_rate * self.channels * 4)  # 4 seconds
        self.ringbuffer = deque(maxlen=ringbuffer_size)

    def callback(self, indata, frames, time, status):
        self.ringbuffer.extend(indata.flatten())

    def _record_segment(self, transcribe):
        start_time = datetime.now()
        while not self.stop_recording:
            segment_length = self.sample_rate * self.intervals * self.channels
            if len(self.ringbuffer) >= segment_length:
                data = np.array([self.ringbuffer.popleft() for _ in range(segment_length)])
                data = data.reshape(-1, self.channels)
                if data.shape[0] > 15:
                    clean_data = self.clean_audio(data)
                else:
                    clean_data = data
                self.all_audio_data = np.vstack([self.all_audio_data, data])

                if self.should_transcribe_segment(start_time):
                    self.handle_transcription(clean_data, transcribe)
                    start_time = datetime.now()

    def start_recording(self):
        self.recording = sd.InputStream(samplerate=self.sample_rate, channels=self.channels, callback=self.callback)
        self.recording.start()
        keyboard.add_hotkey("q", self.set_stop_recording)

    def clean_audio(self, data):
        b, a = butter(4, 0.5, "high")
        return filtfilt(b, a, data, axis=0)

    def stop_recording_function(self):
        self.recording.stop()
        keyboard.clear_hotkey("q")

    def initialize_segment(self):
        start_time = datetime.now()
        data_array_size = (self.sample_rate * self.intervals, self.channels)
        return start_time, 0, np.empty(data_array_size, dtype=np.float32)

    def update_data(self, frames, index, data):
        end_index = index + frames.shape[0]
        if end_index >= data.shape[0]:
            new_data = np.empty((end_index, data.shape[1]), dtype=np.float32)
            new_data[: data.shape[0], :] = data
            data = new_data
        data[index:end_index, :] = frames
        return end_index, data

    def should_transcribe_segment(self, start_time):
        segment_duration = (datetime.now() - start_time).seconds
        return segment_duration >= self.intervals

    def handle_transcription(self, data_slice, transcribe):
        if transcribe:
            transcript = self.voice_transcript(data_slice)
            self.conversation += transcript + " "
            self.check_stop_words(transcript)

    def reset_segment_data(self):
        data_array_size = (self.sample_rate * self.intervals, self.channels)
        return 0, np.empty(data_array_size, dtype=np.float32)

    def cleanup(self):
        self.stop_recording_function()
        if self.audio_file:
            os.remove(self.audio_file)
        if self.transcript_file_path:
            os.remove(self.transcript_file_path)

    def final_output(self, transcribe):
        if transcribe:
            write_to_txt_file(
                self.conversation,
                file_name=self.transcript_file_name,
                output_directory=self.text_file_dir,
                mode="write",
            )
            return self.conversation
        else:
            self.write_to_wav_file(self.all_audio_data, filename=self.filename)
            return self.audio_file

    def write_to_wav_file(self, data, filename=None):
        filename = filename or self.filename
        path = os.path.join(self.output_directory, f"{filename}.wav")
        sf.write(path, data, self.sample_rate)
        return path

    def set_stop_recording(self):
        self.stop_recording = True

    def check_stop_words(self, text: str):
        if any(stop_word in text for stop_word in self.stop_words):
            self.set_stop_recording()

    def voice_transcript(self, audio_data):
        # Create a temporary mp3 file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
            sf.write(temp_path, audio_data, self.sample_rate)

        # Pass the temporary file to call_whisper
        transcript = call_whisper(self.whisper_api_key, temp_path)

        # Remove the temporary file
        os.remove(temp_path)

        return transcript


# class AudioRecorder:
#     def __init__(
#         self,
#         filename,
#         output_directory,
#         duration=600,  # seconds
#         intervals=3,  # seconds
#         sample_rate=44100,
#         channels=2,
#         stop_words: list[str] = None,
#         whisper_api_key=None,
#         transcript_file_name=None,
#         conversation_file_name=None,
#         text_file_dir=None,
#     ):
#         self.filename = filename
#         self.output_directory = output_directory
#         self.duration = duration
#         self.intervals = intervals
#         self.sample_rate = sample_rate
#         self.channels = channels
#         self.stop_recording = False
#         self.stop_words = stop_words if isinstance(stop_words, list) else [stop_words]
#         self.whisper_api_key = whisper_api_key
#         self.transcript_file_name = transcript_file_name
#         self.conversation_file_name = conversation_file_name
#         self.text_file_dir = text_file_dir
#         self.conversation = ""
#         self.all_audio_data = np.array([], dtype=np.float32).reshape(0, self.channels)

#         self.audio_file = None
#         self.transcript_file_path = None

#     def record(self, transcribe=False):
#         try:
#             total_duration = 0
#             self.stop_words = [word.casefold() for word in self.stop_words]

#             while total_duration < self.duration:
#                 self.recording = sd.InputStream(samplerate=self.sample_rate, channels=self.channels)
#                 self.recording.start()
#                 start_time = datetime.now()
#                 data = []
#                 keyboard.add_hotkey("q", self.set_stop_recording)

#                 # Preallocate array for performance increase
#                 data_array_size = (self.sample_rate * self.intervals, self.channels)
#                 data = np.empty(data_array_size, dtype=np.float32)
#                 index = 0

#                 segment_duration = 0
#                 transcript = ""
#                 logger.debug(f'Recording started at {start_time.strftime("%H:%M:%S")}')
#                 while True:
#                     frames, _ = self.recording.read(self.sample_rate)
#                     data[index : index + len(frames)] = frames

#                     index += len(frames)
#                     segment_duration = (datetime.now() - start_time).seconds

#                     if segment_duration >= self.intervals:
#                         self.audio_file = self.write_to_wav_file(data[:index])
#                         self.all_audio_data = np.vstack([self.all_audio_data, data])
#                         index = 0  # Reset index
#                         data = np.empty(data_array_size, dtype=np.float32)  # Reset data
#                         if transcribe:
#                             transcript = self.voice_transcript(self.audio_file).casefold()
#                             self.conversation += f" {transcript}"
#                             self.check_stop_words(transcript)
#                             self.transcript_file_path = os.path.join(self.text_file_dir, f"{self.transcript_file_name}.txt")

#                     if self.stop_recording:
#                         break

#                 self.recording.stop()
#                 logger.debug(f'Recording stopped at {datetime.now().strftime("%H:%M:%S")}')
#                 keyboard.clear_hotkey("q")
#                 self.stop_recording = False  # Reset for the next segment

#             if transcribe:
#                 write_to_txt_file(
#                     self.conversation,
#                     file_name=self.conversation_file_name,
#                     output_directory=self.text_file_dir,
#                     mode="write",
#                 )

#             if transcribe:
#                 return self.conversation
#             else:
#                 return self.audio_file
#         except Exception as e:
#             log_exception(e)
#         finally:
#             self.cleanup_files()
#             self.write_to_wav_file(self.all_audio_data, filename=f"full_{self.filename}")

#     def write_to_wav_file(self, data, filename=None):
#         filename = filename or self.filename
#         path = os.path.join(self.output_directory, f"{filename}.wav")
#         sf.write(path, data, self.sample_rate)
#         return path

#     def set_stop_recording(self):
#         self.stop_recording = True

#     def check_stop_words(self, text: str):
#         if any(stop_word in text for stop_word in self.stop_words):
#             self.set_stop_recording()

#     def voice_transcript(self, output_audio_file):
#         transcript = call_whisper(self.whisper_api_key, output_audio_file)

#         write_to_txt_file(
#             transcript,
#             file_name=self.transcript_file_name,
#             output_directory=self.text_file_dir,
#             mode="write",
#         )
#         print(transcript, end=" ", flush=True)
#         return transcript

#     def cleanup_files(self):
#         if self.audio_file:
#             logger.debug(f"Attempting to delete {self.audio_file}")
#             os.remove(self.audio_file)
#         if self.transcript_file_path:
#             logger.debug(f"Attempting to delete {self.transcript_file_path}")
#             os.remove(self.transcript_file_path)


# GEN3 (SHIT)
class ContinuousRecorder:
    def __init__(
        self,
        sample_rate=44100,
        channels=2,
        interval=3,
        output_dir="output",
        whisper_api_key=None,
        silence_thresh=-40,
        silence_len=700,
    ):
        self.q = queue.Queue()
        self.sample_rate = sample_rate
        self.channels = channels
        self.interval = interval
        self.output_dir = output_dir
        self.whisper_api_key = whisper_api_key
        self.all_audio_data = np.empty((0, self.channels), dtype=np.float32)
        self.transcripts = []
        self.silence_thresh = silence_thresh
        self.silence_len = silence_len

    def _callback(self, indata, frames, time, status):
        self.q.put(indata.copy())

    def _detect_silence(self, audio_segment):
        return detect_silence(audio_segment, min_silence_len=self.silence_len, silence_thresh=self.silence_thresh)

    def record(self, max_time=60, max_silence=6):
        index = 0
        start_time = time.time()
        silence_counter = 0
        segment_data = np.empty((self.sample_rate * self.interval, self.channels), dtype=np.float32)  # Initialize here

        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, callback=self._callback):
            audio_segment = AudioSegment.silent(duration=0)

            while True:
                chunk = self.q.get()
                segment_data[index : index + len(chunk)] = chunk
                audio_chunk = AudioSegment(
                    data=chunk.tobytes(),
                    sample_width=chunk.dtype.itemsize,
                    frame_rate=self.sample_rate,
                    channels=self.channels,
                )
                audio_segment += audio_chunk

                if self._detect_silence(audio_segment):
                    self.all_audio_data = np.vstack([self.all_audio_data, segment_data])
                    if self.whisper_api_key:
                        transcript = self._process_with_whisper(segment_data)
                        self.transcripts.append(transcript)
                    audio_segment = AudioSegment.silent(duration=0)

                    index = 0
                    silence_counter += self.interval  # Increment silence counter

                if time.time() - start_time >= max_time or silence_counter >= max_silence:
                    break

    def _write_to_wav(self):
        self.filename = datetime.now().strftime("%Y%m%d%H%M%S")
        filepath = os.path.join(self.output_dir, f"{self.filename}.wav")
        sf.write(filepath, self.all_audio_data, self.sample_rate)

    def _process_with_whisper(self, audio_data):
        transcript = call_whisper(self.whisper_api_key, audio_data)
        print(transcript, end=" ", flush=True)
        return transcript

    def stop(self):
        self._write_to_wav()
        audio_file_path = os.path.join(self.output_dir, f"{self.filename}.wav")
        text_file_path = "transcripts.txt"
        with open(text_file_path, "w") as f:
            f.write(" ".join(self.transcripts))
        return audio_file_path, text_file_path
