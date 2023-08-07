import logging
from ..utility.logger import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

from dotenv import load_dotenv
import os
import json
from termcolor import colored


def load_settings(settings_path, dotenv_path=None):
    # Initialize an empty dictionary for secrets
    secrets_dict = {}

    print(colored(f"Loading settings from {settings_path}", "cyan"))

    # Load .env variables if load_secrets is True
    if dotenv_path:
        print(colored(f"Loading secrets from {dotenv_path}", "cyan"))
        load_dotenv(dotenv_path)

        secrets_dict = {
            "AIRTABLE_API_TOKEN": os.getenv("AIRTABLE_API_TOKEN"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "DALLEE_API_KEY": os.getenv("DALLEE_API_KEY"),
            "EVENTBRITE_PRIVATE_TOKEN": os.getenv("EVENTBRITE_PRIVATE_TOKEN"),
            "XANO_API_KEY": os.getenv("XANO_API_KEY"),
            "XANO_ENDPOINT_POST": os.getenv("XANO_ENDPOINT_POST"),
            "XANO_ENDPOINT_IMAGE": os.getenv("XANO_ENDPOINT_IMAGE"),
            "XANO_ENDPOINT_GET_ALL": os.getenv("XANO_ENDPOINT_GET_ALL"),
            "XANO_ENDPOINT_EDIT": os.getenv("XANO_ENDPOINT_EDIT"),
            "XANO_ENDPOINT_DELETE": os.getenv("XANO_ENDPOINT_DELETE"),
            "XANO_TABLE_NAME": os.getenv("XANO_TABLE_NAME"),
            "LINKEDIN_USER": os.getenv("LINKEDIN_USER"),
            "LINKEDIN_PWORD": os.getenv("LINKEDIN_PWORD"),
        }

    # Check if the settings file exists
    if not os.path.exists(settings_path):
        raise FileNotFoundError(f"Settings file not found: {settings_path}")

    # Load the settings dictionary from the .json file
    with open(settings_path, "r") as fp:
        settings_dict = json.load(fp)

    # Merge the API keys and other settings
    settings_dict.update(secrets_dict)

    return settings_dict
