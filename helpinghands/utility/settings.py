import logging
from ..utility.logger import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

from dotenv import load_dotenv
import os
import json
from termcolor import colored


def load_settings(
    dotenv_settings_path="SETTINGS_PATH",
    secrets_keys_list=None,
    dotenv_path=None,
    remote_env="DOCKER_ENV",
    default_settings_path="data/settings.json",
):
    # Initialize an empty dictionary for secrets
    secrets_dict = {}

    try:
        if os.getenv(remote_env) is None:
            if dotenv_path:
                load_dotenv(dotenv_path)
            else:
                load_dotenv()
            logger.debug(colored("Loaded local .env file", "cyan"))

        # Load .env variables if keys are provided
        if secrets_keys_list:
            for secret_key in secrets_keys_list:
                value = os.getenv(secret_key)
                if value:
                    secrets_dict[secret_key] = value
                else:
                    logger.warning(f"Missing environment variable: {secret_key}")

            logger.debug(
                colored(f"Loaded secrets: {', '.join(secrets_keys_list)}", "cyan")
            )

        # Fetch settings path either from the environment or use the default one
        settings_path = os.getenv(dotenv_settings_path, default_settings_path)

        # Check if the settings file exists
        if not os.path.exists(settings_path):
            raise FileNotFoundError(f"Settings file not found: {settings_path}")

        logger.info(colored(f"Loading settings from {settings_path}", "cyan"))

        # Load the settings dictionary from the .json file
        with open(settings_path, "r") as fp:
            settings_dict = json.load(fp)

        # Merge the API keys and other settings
        settings_dict.update(secrets_dict)

        return settings_dict

    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from settings file: {settings_path}")
        raise
    except Exception as e:
        logger.error(f"Unexpected {type(e).__name__}: {e}")
        raise
