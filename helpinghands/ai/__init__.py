from .whisper import call_whisper
from .gpt import chat
from .dalle import generate_image
from .assistant import have_conversation
from .tts import text_to_speech
from .setup import init_openai_client
from .vision import view_image, image_description_iteration

try:
    from .upscale import super_image, super_image_loop
except ModuleNotFoundError:
    import warnings

    warnings.warn("'ai.upscale' is disabled")
