from openai import OpenAI
from dotenv import load_dotenv
import os


# openai
def init_openai_client(raw_api_key=None, dotenv_key=None):
    load_dotenv()

    api_key = (
        os.getenv(dotenv_key)
        if dotenv_key and dotenv_key != "OPENAI_API_KEY"
        else raw_api_key
    )

    return OpenAI(api_key=api_key)
