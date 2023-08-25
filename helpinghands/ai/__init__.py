from .whisper import call_whisper
from .gpt import call_gpt, gpt_loop
from .dallee import generate_image, dallee_loop

try:
    from .upscale import super_image, super_image_loop
except ModuleNotFoundError:
    import warnings

    warnings.warn("'ai.upscale' is disabled")
