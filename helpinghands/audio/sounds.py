from ..utility import ensure_windows_os

import platform

if platform.system() == "Windows":
    import winsound


def uhoh():
    """Plays an 'uhoh' sound using winsound. Only works on Windows."""
    ensure_windows_os()
    winsound.Beep(frequency=900, duration=300)
    winsound.Beep(frequency=600, duration=200)


def criterr():
    """Plays a 'criterr' sound using winsound. Only works on Windows."""
    ensure_windows_os()
    winsound.Beep(frequency=600, duration=600)
    winsound.Beep(frequency=400, duration=800)
    winsound.Beep(frequency=200, duration=1000)


def warning():
    """Plays a 'warning' sound using winsound. Only works on Windows."""
    ensure_windows_os()
    winsound.Beep(frequency=1000, duration=100)
    winsound.Beep(frequency=1200, duration=200)
    winsound.Beep(frequency=1000, duration=100)
    winsound.Beep(frequency=1200, duration=200)


def success():
    """Plays a 'success' sound using winsound. Only works on Windows."""
    ensure_windows_os()
    winsound.Beep(frequency=1000, duration=200)
    winsound.Beep(frequency=1400, duration=200)
    winsound.Beep(frequency=1600, duration=200)
