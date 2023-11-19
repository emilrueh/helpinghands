import numpy as np
from scipy.io.wavfile import write
import os
from pydub import AudioSegment


def synthesize_drum(sound_type, duration, sample_rate=44100):
    """
    Synthesize a basic drum sound.
    :param sound_type: Type of drum sound ('kick', 'snare', etc.)
    :param duration: Duration of the sound in seconds.
    :param sample_rate: Sample rate.
    :return: NumPy array of the synthesized drum sound.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    if sound_type == "kick":
        # Basic kick drum sound synthesis
        frequency = 50  # Low frequency for kick drum
        envelope = np.e ** (-5 * t)  # Exponential decay
        waveform = np.sin(2 * np.pi * frequency * t) * envelope
    elif sound_type == "snare":
        # Basic snare drum sound synthesis
        noise = np.random.normal(0, 1, len(t))  # White noise
        envelope = np.e ** (-10 * t)  # Faster decay than kick
        waveform = noise * envelope
    # ... add other drum types if needed
    else:
        waveform = np.zeros_like(t)  # Silent if type not recognized

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
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        waveform = np.sin(note * 2 * np.pi * t)
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
    drum_pattern=["kick", "snare"],
    melody_notes=["C3", "B5", "E2", "G6"],
    song_length=10,
    bpm=120,
    sample_rate=44100,
    output_file="gen_music.wav",
):
    """
    Generates a complete music track with both drum and melody based on the given parameters.

    :param drum_pattern: List of drum types to be included in the drum track.
    :param melody_notes: List of note names for the melody.
    :param bpm: Beats per minute, determining the tempo of the track.
    :param song_length: Total length of the song in seconds.
    :param output_file: File path to save the generated music track.
    :param sample_rate: Sampling rate for the audio.
    """
    melody_freqs = [note_to_freq(note) for note in melody_notes]

    drum_track = generate_track(
        drum_pattern, bpm, song_length, sample_rate, track_type="drum"
    )
    melody_track = generate_track(
        melody_freqs, bpm, song_length, sample_rate, track_type="melody"
    )

    combined_track = mix_tracks(drum_track, melody_track)

    # Normalize to 16-bit range and convert to int16
    combined_track *= (2**15 - 1) / np.max(np.abs(combined_track))
    combined_track = combined_track.astype(np.int16)

    # Write to a WAV file
    write(output_file, sample_rate, combined_track)
