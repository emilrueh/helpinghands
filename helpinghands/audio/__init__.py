try:
    from .sounds import uhoh, criterr, warning, success
    from .converter import convert_audio, combine_audio_files
    from .recorder import AudioRecorder  # ContinuousRecorder
    from .processing import (
        play_sound,
        get_tempo,
        match_tempo,
        bpm_match_two_files,
        get_audio_length,
    )
    from .music import generate_music

except (ImportError, OSError) as e:
    import warnings

    warnings.warn(f"'audio' is disabled ({type(e).__name__}{e})")
