from gtts import gTTS
from dotenv import load_dotenv

import os, pathlib, random

from .assistant import init_openai_client

client = init_openai_client()


def openai_tts(
    input_text, output_file_path="./oa-tts_output.mp3", model="tts-1", voice="alloy"
):
    # processing
    response = client.audio.speech.create(model=model, voice=voice, input=input_text)

    # saving
    response.stream_to_file(output_file_path)

    return output_file_path


def google_tts(input_text, output_file_path="./gtts_output.mp3", lang="en"):
    # processing
    tts = gTTS(input_text=input_text, lang=lang)

    # saving
    tts.save(output_file_path)

    return output_file_path


# re-usable implementation
def text_to_speech(text, output_directory, tts_provider=None, voice=None) -> str:
    """
    Returns: file path in .mp3 or .wav

    Choose tts_provider: (or specify in .env key "TTS_PROVIDER")
        1. gtts: basic google tts library
        2. openai: advanced AI tts API endpoint
    """

    output_dir_obj = pathlib.Path(output_directory)

    # load tts_provider from dotenv if not given
    if tts_provider is None:
        load_dotenv()
        tts_provider = os.getenv("TTS_PROVIDER")

    # creating voice audio file
    if tts_provider == "gtts":
        voice_file_path = google_tts(text, output_directory)

    elif tts_provider == "openai":
        # choose random voice if not given
        voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if voice is None:
            voice = random.choice(voices)
        print(f"OpenAI TTS Voice: {voice}")

        voice_file_path = openai_tts(
            text, output_dir_obj / "oa_tts_output.mp3", voice=voice
        )

    else:
        print("Unknown TTS provider specified. Returning...")
        return

    return voice_file_path
