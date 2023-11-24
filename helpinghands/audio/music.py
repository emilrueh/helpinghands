import numpy as np
from scipy.io.wavfile import write

import random, pathlib

from ..utility.data import choose_random_file
from ..audio.processing import (
    bpm_match_two_files,
    play_sound,
    get_audio_length,
)


def synth_kick(time, sample_rate):
    # Enhanced kick drum sound synthesis
    start_frequency = 250  # Starting frequency for pitch drop
    end_frequency = 70  # End frequency after drop
    pitch_drop_duration = 0.05  # Duration of pitch drop
    pitch_drop_t = np.linspace(
        0, pitch_drop_duration, int(sample_rate * pitch_drop_duration), False
    )
    stable_time = time[len(pitch_drop_t) :]

    # Create a pitch drop effect
    frequency = np.linspace(start_frequency, end_frequency, len(pitch_drop_t))
    frequency = np.concatenate([frequency, np.full_like(stable_time, end_frequency)])

    envelope = np.e ** (-4 * time)  # Adjusted decay
    waveform = np.sin(2 * np.pi * frequency * time) * envelope

    return waveform


def synth_snare(time, sample_rate):
    # Basic snare drum sound synthesis
    noise = np.random.normal(0, 1, len(time))  # White noise
    envelope = np.e ** (-10 * time)  # Faster decay than kick
    waveform = noise * envelope

    return waveform


def synth_highhat(time, style):
    noise = np.random.normal(0, 1, len(time))  # White noise for high-hat

    if style == "open":
        decay = -40  # long decay
    elif style == "closed":
        decay = -5  # short decay

    envelope = np.e ** (decay * time)
    waveform = noise * envelope

    return waveform


def synthesize_drum(sound_type, duration, sample_rate=44100):
    """
    Synthesize a basic drum sound.
    :param sound_type: Type of drum sound ('kick', 'snare', etc.)
    :param duration: Duration of the sound in seconds.
    :param sample_rate: Sample rate.
    :return: NumPy array of the synthesized drum sound.
    """
    time = np.linspace(0, duration, int(sample_rate * duration), False)

    if sound_type == "kick":
        waveform = synth_kick(time, sample_rate)

    elif sound_type == "snare":
        waveform = synth_snare(time, sample_rate)

    elif sound_type in ["closed_hat", "open_hat"]:
        if sound_type == "closed_hat":
            waveform = synth_highhat(time, "closed")
        elif sound_type == "open_hat":
            waveform = synth_highhat(time, "open")

    # ... add other drum types if needed
    else:
        waveform = np.zeros_like(time)  # Silent if type not recognized

    return waveform


def synthesize_melody(notes, duration, sample_rate=44100):
    """
    Synthesize a melody from a sequence of notes.
    :param notes: List of notes as frequencies (in Hz).
    :param duration: Duration of each note in seconds.
    :param sample_rate: Sampling rate.
    :return: NumPy array of the synthesized melody.
    """
    melody = np.array([])
    for note in notes:
        time = np.linspace(0, duration, int(sample_rate * duration), False)
        waveform = np.sin(note * 2 * np.pi * time)
        melody = np.concatenate((melody, waveform))

    return melody


def note_to_freq(note):
    """
    Convert a musical note to its frequency.
    :param note: String representing the note (e.g., 'A4', 'C5', etc.)
    :return: Frequency in Hz.
    """
    # Notes in an octave
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Parse the note and its octave
    note, octave = note[:-1], int(note[-1])

    # Calculate the index of the note
    n = notes.index(note)

    # Calculate the frequency
    frequency = 440.0 * (2 ** ((n - 9 + (12 * (octave - 4))) / 12))
    return frequency


def generate_track(pattern, bpm, song_length, sample_rate, track_type="melody"):
    """
    Generates a track (either drum or melody) based on a given pattern and BPM.

    :param pattern: List of elements (frequencies for melody, drum types for drum track).
    :param bpm: Beats per minute, determining the tempo of the track.
    :param song_length: Length of the song in seconds.
    :param sample_rate: Sampling rate for the audio.
    :param track_type: Type of the track to generate ('melody' or 'drum').
    :return: NumPy array representing the generated track.
    """
    bpm = bpm * 2  # adjusting bpm for correct temp

    beat_duration = 60 / bpm  # Duration of a single beat in seconds
    track = np.array([])

    # Calculate the total number of beats in the song
    total_beats = int(song_length * bpm / 60)

    # Calculate how many times the pattern should repeat to fill the song
    pattern_length = len(pattern)
    repetitions = (total_beats + pattern_length - 1) // pattern_length

    for _ in range(repetitions):
        for element in pattern:
            if track_type == "melody":
                # Generate waveform for each note in the melody
                note_waveform = synthesize_melody([element], beat_duration, sample_rate)
                track = np.concatenate((track, note_waveform))
            elif track_type == "drum":
                # Generate drum sound for each element in the drum pattern
                drum_sound = synthesize_drum(element, beat_duration, sample_rate)
                track = np.concatenate((track, drum_sound))

    # Trim the track to the exact song length
    required_length = int(sample_rate * song_length)
    track = track[:required_length]

    return track


def mix_tracks(drum_track, melody_track):
    """
    Mixes the drum and melody tracks into a single track.

    :param drum_track: The drum track as a NumPy array.
    :param melody_track: The melody track as a NumPy array.
    :return: Combined NumPy array of the mixed track.
    """
    combined_length = max(len(drum_track), len(melody_track))
    combined_track = np.zeros(combined_length)
    combined_track[: len(drum_track)] += drum_track
    combined_track[: len(melody_track)] += melody_track
    return combined_track


# re-usable implementation
def generate_music(
    drum_patterns=None,  # List of drum patterns
    melody_sequences=None,  # List of melody sequences
    song_length=9,
    bpm=None,
    sample_rate=44100,
    output_file="gen_music.wav",
):
    """
    Generates a complete music track with multiple drum and melody tracks based on the given parameters.

    :param drum_patterns: List of drum patterns, each a list of drum types for a separate drum track.
    :param melody_sequences: List of melody sequences, each a list of note names for a separate melody track.
    :param bpm: Beats per minute, determining the tempo of the track.
    :param song_length: Total length of the song in seconds.
    :param output_file: File path to save the generated music track.
    :param sample_rate: Sampling rate for the audio.
    """

    if drum_patterns is None:
        drum_patterns = create_pattern(create_drum_pattern)
    if melody_sequences is None:
        melody_sequences = create_pattern(create_melody_sequence)
    if bpm is None:
        bpm = random.randint(90, 140)

    # Initialize an empty array for the final mix
    final_mix = np.array([])

    # Generate and mix all drum tracks
    for pattern in drum_patterns:
        drum_track = generate_track(
            pattern, bpm, song_length, sample_rate, track_type="drum"
        )
        if len(final_mix) == 0:
            final_mix = drum_track
        else:
            final_mix = mix_tracks(final_mix, drum_track)

    # Generate and mix all melody tracks
    for sequence in melody_sequences:
        melody_freqs = [note_to_freq(note) for note in sequence]
        melody_track = generate_track(
            melody_freqs, bpm, song_length, sample_rate, track_type="melody"
        )
        final_mix = mix_tracks(final_mix, melody_track)

    # Normalize to 16-bit range and convert to int16
    final_mix *= (2**15 - 1) / np.max(np.abs(final_mix))
    final_mix = final_mix.astype(np.int16)

    # Write to a WAV file
    write(output_file, sample_rate, final_mix)

    return output_file


# random pattern generation for above music generation functions


def create_drum_pattern(pattern_type):
    # Selection of drum type
    drum_choices = {
        "lows": ["kick", ""],
        "highs": ["snare", "open_hat", "closed_hat", ""],
    }

    # Choose setup based on pattern type
    drum_count = random.choice([2, 4, 6, 8])
    drum_pattern = [
        random.choice(drum_choices[pattern_type]) for _ in range(drum_count)
    ]

    return drum_pattern


def create_melody_sequence(pattern_type):
    # Adjusting the note generation based on pattern_type
    if pattern_type == "bass":
        pitch_choices = [0, 2]
        notes_count = random.choice([2, 4])
    else:  # pattern_type == "melody"
        pitch_choices = [0, 4, 5]
        notes_count = random.choice([4, 8])

    # General note setup
    notes = ["C", "D", "E", "F", "G", "A", "B"]
    melody_sequence = [
        random.choice(notes) + str(random.choice(pitch_choices))
        for _ in range(notes_count)
    ]

    return melody_sequence


def validate_drum_pattern(pattern):
    """
    Validates a drum pattern to ensure it is not composed entirely of empty strings.
    :param pattern: The drum pattern to validate.
    :return: Boolean indicating whether the pattern is valid.
    """
    return any(element for element in pattern if element != "")


def validate_melody_sequence(sequence):
    """
    Validates a melody sequence to ensure it does not consist exclusively of notes ending with '0'.
    :param sequence: The melody sequence to validate.
    :return: Boolean indicating whether the sequence is valid.
    """
    return any(note[-1] != "0" for note in sequence)


def create_pattern(function):
    """
    Creates multiple valid patterns using the specified creation function.
    For melody, it automatically creates one melody and one bass line pattern.

    :param function: Function used to create a single pattern.
    :param min_count: Minimum number of patterns to create (only for melody).
    :param max_count: Maximum number of patterns to create (only for melody).
    :return: A list of valid patterns.
    """
    patterns = []

    if "drum" in function.__name__:
        # For drum patterns, always create one low and one high
        for pattern_type in ["lows", "highs"]:
            while True:
                pattern = function(pattern_type)
                if validate_drum_pattern(pattern):
                    patterns.append(pattern)
                    break

    elif "melody" in function.__name__:
        # For melody patterns, create one melody and one bass line
        for pattern_type in ["melody", "bass"]:
            while True:
                pattern = create_melody_sequence(pattern_type)
                if validate_melody_sequence(pattern):
                    patterns.append(pattern)
                    break

    else:
        raise ValueError("Unknown pattern creation function")

    return patterns


# WIP:


def voice_and_music(
    voice_input_file_path,
    output_dir,
    music_style: str = "generated",
    bpm: int = 120,
):
    voice_length = get_audio_length(voice_input_file_path)

    output_dir_obj = pathlib.Path(output_dir)

    # check and create dirs
    adjusted_bpm_dir = output_dir_obj / "adjusted_bpm"
    adjusted_bpm_dir.mkdir(parents=True, exist_ok=True)

    # MUSIC SELECTION
    if music_style == "random":
        print("Choosing random music...")
        # choosing random file from dir
        music_file_path = choose_random_file(output_dir_obj)
    else:
        print("Generating music...")
        music_file_path = generate_music(
            song_length=voice_length,
            bpm=bpm,
            output_file=output_dir_obj / "gen_music.wav",
        )
    print(f"Music file path: {music_file_path}")

    # bpm matching of the two files
    new_voice_path, new_music_path = bpm_match_two_files(
        file_path_one=voice_input_file_path,
        file_path_two=music_file_path,
        output_dir=adjusted_bpm_dir,
        tempo=bpm,
    )

    # playing voice
    play_sound(new_voice_path)

    # playing music (at lower volume)
    play_sound(new_music_path, volume=0.2)
