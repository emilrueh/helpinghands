from openai import OpenAI
from dotenv import load_dotenv

from gtts import gTTS

import os


load_dotenv()

client = OpenAI()


def openai_tts(
    input_text, output_file_path="./oa-tts_output.mp3", model="tts-1", voice="alloy"
):
    # processing
    response = client.audio.speech.create(model=model, voice=voice, input=input_text)

    # saving
    response.stream_to_file(output_file_path)

    return output_file_path


def gtts_tts(input_text, output_file_path="./gtts_output.mp3", lang="en"):
    # processing
    tts = gTTS(input_text=input_text, lang=lang)

    # saving
    tts.save(output_file_path)

    return output_file_path
