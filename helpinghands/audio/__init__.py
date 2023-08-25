try:
    from .sounds import uhoh, criterr, warning, success
    from .converter import convert_audio, combine_audio_files
    from .recorder import AudioRecorder
except (ImportError, OSError):
    import warnings

    warnings.warn("'audio' is disabled")
