# HelpingHands Library

The HelpingHands library provides various modules for different AI integration related "every-day" functionalities using Python.

<div align="center">
    <img src="https://github.com/emilrueh/helpinghands/blob/dev/helpinghands_logo_v1.png" alt="HelpingHands Library Logo - A modern cyberpunk style logo featuring stylized hands and digital elements representing software development" width="420">
</div>

## Table of Contents
- [Introduction](#helpinghands-library)
- [Modules](#modules)
  - [AI](#ai)
  - [Audio](#audio)
  - [Data](#data)
  - [Utility](#utility)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)
- [Author](#author)

---

## Modules

> This modules section will give a grand overview over all submodules and the functions meant to be called from projects using this library.

### 🤖 AI
#### whisper.py
- `call_whisper()`: Calls the Whisper endpoint for audio transcription.

#### gpt.py
- `chat()`: Interacts with the GPT endpoint for text-based conversations.

#### dalle.py
- `generate_image()`: Generates images using the DALLE model.

#### assistant.py
- `have_conversation()`: Facilitates an AI-powered conversation.

#### tts.py
- `text_to_speech()`: Converts text to speech.

#### setup.py
- `init_openai_client()`: Initializes the OpenAI client.

#### vision.py
- `view_image()`: Views an image.
- `image_description_iteration()`: Iteratively describes images.

#### upscale.py
- `super_image()`: Upscales images using AI.
- `super_image_loop()`: Continuously upscales images.

---

### 🎶 AUDIO
#### sounds.py
- `uhoh()`: Plays "uh-oh" sound.
- `criterr()`: Plays critical error sound.
- `warning()`: Plays warning sound.
- `success()`: Plays success sound.

#### converter.py
- `convert_audio()`: Converts audio files between different formats.
- `combine_audio_files()`: Combines multiple audio files into one.

#### recorder.py
- `AudioRecorder()`: Class for recording audio.

#### processing.py
- `play_sound()`: Plays a sound file.
- `get_tempo()`: Gets the tempo (BPM) of an audio file.
- `match_tempo()`: Matches the tempo of an audio file to a given BPM.
- `bpm_match_two_files()`: Matches the tempo between two audio files.
- `get_audio_length()`: Retrieves the length of an audio file.

#### music.py
- `generate_music()`: Generates music based on specified parameters.

---

### 💾 DATA
#### various.py
- `get_data_dir()`: Retrieves the data directory.
- `add_random_files()`: Adds random files to a directory.
- `choose_random_file()`: Chooses a random file from a directory.
- `clean_directory()`: Cleans a specified directory.
- `remove_duplicate_words()`: Removes duplicate words from text.
- `extract_number()`: Extracts a number from text.
- `json_save()`: Saves data in JSON format.
- `json_read()`: Reads data from a JSON file.
- `json_to_df()`: Converts JSON data to a DataFrame.
- `create_df()`: Creates a new DataFrame.
- `df_from_csv()`: Creates a DataFrame from a CSV file.
- `backup_df()`: Backs up a DataFrame.

#### text.py
- `insert_newlines()`: Inserts new lines into text.
- `write_to_txt_file()`: Writes text to a TXT file.
- `load_text_from_file()`: Loads text from a file.
- `open_txt_file()`: Opens a TXT file.

#### image.py
- `convert_byte_sizes()`: Converts byte sizes.
- `get_image_res()`: Gets the resolution of an image.
- `get_image()`: Retrieves an image.
- `image_to_bytes()`: Converts an image to bytes.
- `bytes_to_base64()`: Converts bytes to base64.
- `image_to_base64str()`: Converts an image to a base64 string.
- `get_file_size()`: Gets the file size of an image.
- `compress_image()`: Compresses an image.

---

### 🧰 UTILITY
#### settings.py
- `load_settings()`: Loads settings from specified paths.

#### logger.py
- `config_logger()`: Configures the logger.
- `LOGGER_NAME`: A constant defining the logger name.

#### tokenbucket.py
- `TokenBucket()`: Implements a token bucket algorithm.
- `api_rate_limit_wait()`: Waits based on the token bucket for API rate limiting.

#### decorator.py
- `retry()`: A decorator for retrying functions.
- `time_execution()`: Times the execution of a function.

#### helper.py
- `log_exception()`: Logs exceptions.
- `get_git_tree()`: Retrieves the Git tree of a repository.
- `colorize()`: Adds color to text.
- `get_variable_name()`: Gets the name of a variable as a string.
- `ensure_windows_os()`: Ensures the OS is Windows.
- `log_memory_usage()`: Logs memory usage.

#### web.py
- `WebConfig()`: Class for configuring web settings.
- `open_website()`: Opens a specified website.
- `setup_browser()`: Sets up the browser.
- `setup_proxy_wire()`: Sets up a selenium-wire proxy.
- `setup_proxy_simple()`: Sets up a simple proxy.
- `test_proxy()`: Tests the proxy configuration.
- `listen_on_port()`: Listens on a specified port.
- `get_original_ip()`: Gets the original IP address.
- `get_current_ip()`: Gets the current IP address.
- `rotate_ip()`: Rotates the IP address.
- `make_soup()`: Makes a BeautifulSoup object for web parsing.
- `connect_to_vpn()`: Connects to a VPN.
- `disconnect_from_vpn()`: Disconnects from a VPN.
- `check_internet()`: Checks the internet connection.

---

## Installation

To install the HelpingHands library, you will need to clone this repo and install it in editable mode with pip:

`git clone https://github.com/emilrueh/helpinghands.git`

`pip install -e path/to/lib/directory`

## Usage

Here's an example of how the library might be used with an example definition of a function for audio transcription using the OpenAI's whisper model:

```python
from helpinghands.utility.logger import config_logger

logger = config_logger()

from helpinghands.utility.settings import load_settings

from helpinghands.audio import sounds
from helpinghands.utility.decorator import retry, time_execution
from helpinghands.ai import call_whisper
from helpinghands.utility.helper import log_exception

import os

base_dir = os.path.dirname(__file__)
settings_dir = os.path.join(base_dir, "settings")
audio_dir = os.path.join(base_dir, "audio")

mp3_file = os.path.join(audio_dir, "recording.mp3")
settings_file = os.path.join(settings_dir, "settings.json")

settings = load_settings(
    settings_file=settings_file,
    secrets_keys_list=["API_KEY"],
)

openai_api_key = settings.get("API_KEY")


@time_execution(2, time_mode="seconds")
@retry((Exception), "simple")
def transcribe_audio(api_key, mp3_path, action="transcribe"):
    try:
        output = call_whisper(api_key, mp3_path, action)
        return output
    except Exception as e:
        sounds.uhoh()
        exception_name = log_exception(e)
        raise
  

transcript = transcribe_audio(openai_api_key, mp3_file)
logger.info(f"Transcript:\n{transcript}")
```

## License
This project serves as a demonstration of and it is not intended for cloning or external contributions. We kindly ask that you respect this intention by not using it for commercial purposes or distributing it. This work is licensed under the [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License](https://creativecommons.org/licenses/by-nc-nd/4.0/)

## Author
[Emil Rühmland](https://github.com/emilrueh)