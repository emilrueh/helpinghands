try:
    from .sounds import uhoh, criterr, warning, success
    from .converter import ogg_to_mp3
    from .recorder import AudioRecorder
except (ImportError, OSError):
    import warnings

    warnings.warn(
        "The audio module is disabled in the current env due to missing dependencies. All other helpinghands modules should work as expected."
    )
