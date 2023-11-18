from gtts import gTTS  # text to speech
import librosa  # get tempo
from pydub import AudioSegment  # altering
import pygame  # playing

import os


pygame.mixer.init()


def play_sound(file_path, volume=1.0, wait_to_finish=False):
    # initializing
    sound = pygame.mixer.Sound(file_path)
    # processing
    sound.set_volume(volume)
    # playing
    sound.play()

    # wait for sound to finish playing
    if wait_to_finish:
        while pygame.mixer.get_busy():
            pygame.time.Clock().tick(10)


def speaking(text, output_directory, output_file_name="gtts_output.mp3", lang="en"):
    output_file_path = os.path.join(output_directory, output_file_name)

    # text to speech
    tts = gTTS(text=text, lang=lang)

    tts.save(output_file_path)
    return output_file_path


# tempo matching of voice and beat
def get_tempo(file_path):
    y, sr = librosa.load(file_path)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    # getting tempo
    tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
    return tempo[0]


def match_tempo(original_file, target_tempo, original_tempo):
    # init
    ratio = target_tempo / original_tempo
    sound = AudioSegment.from_file(original_file)

    # altering 'frame rate' (tempo)
    sound_with_altered_frame_rate = sound._spawn(
        sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * ratio)}
    ).set_frame_rate(sound.frame_rate)

    return sound_with_altered_frame_rate


def bpm_match_two_files(file_path_one, file_path_two, output_dir, tempo=120):
    # checking tempo of tracks
    tempo_one = get_tempo(file_path_one)
    tempo_two = get_tempo(file_path_two)

    # changing tempo of tracks
    adj_one = match_tempo(file_path_one, tempo, original_tempo=tempo_one)
    adj_two = match_tempo(file_path_two, tempo, original_tempo=tempo_two)

    # Export the adjusted audio
    adj_filename_one = os.path.basename(file_path_one).replace(".mp3", "_bpm.mp3")
    adj_path_one = os.path.join(output_dir, adj_filename_one)

    adj_filename_two = os.path.basename(file_path_two).replace(".mp3", "_bpm.mp3")
    adj_path_two = os.path.join(output_dir, adj_filename_two)

    # exporting altered music files
    adj_one.export(adj_path_one, format="mp3")
    adj_two.export(adj_path_two, format="mp3")

    return adj_path_one, adj_path_two
