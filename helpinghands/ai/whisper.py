from ..utility.logger import get_logger

import requests, time

import openai


def call_whisper(api_key, mp3_path, action="transcribe"):
    """
    Could need some love regarding other whisper functions
    and the opening of any kind of path format or taking a
    prompt as specified in the OpenAI API docs:
    https://platform.openai.com/docs/guides/speech-to-text/longer-inputs

    """
    logger = get_logger()
    openai.api_key = api_key

    if action.casefold() == "transcribe":
        attempts = 0
        while attempts < 5:
            try:
                with open(rf"{mp3_path}", "rb") as audio_file:
                    api_result = openai.Audio.transcribe("whisper-1", audio_file)["text"]
                if api_result is not None:
                    logger.debug(
                        f"Successfully called the whisper model to {action} from the OpenAI API."
                    )
                    return api_result
                else:
                    return "Something failed and the API result is None."
            except (openai.error.RateLimitError, requests.exceptions.ConnectionError):
                logger.error(
                    f"ERROR encountered. New API call attempt in {(2**attempts)} seconds...\n"
                )
                time.sleep((2**attempts))
                attempts += 1
    else:
        return "Wrongly specified action. Try again."
