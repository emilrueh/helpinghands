try:
    from .sounds import uhoh, criterr, warning, success
    from .converter import convert_audio, combine_audio_files
    from .recorder import AudioRecorder, ContinuousRecorder
except (ImportError, OSError) as e:
    import warnings

    warnings.warn(f"'audio' is disabled ({type(e).__name__}{e})")
