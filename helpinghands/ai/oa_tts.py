from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()


def openai_tts(input_text, output_path="./oa_tts.mp3", model="tts-1", voice="alloy"):
    """
    returns the response from the openai api endpoint
    """
    response = client.audio.speech.create(model=model, voice=voice, input=input_text)
    response.stream_to_file(output_path)
    return output_path
