from openai import OpenAI
from dotenv import load_dotenv

client = OpenAI()


def openai_tts(input_text, model="tts-1", voice="alloy"):
    """
    returns the response from the openai api endpoint
    """
    return client.audio.speech.create(model=model, voice=voice, input=input_text)
