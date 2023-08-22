# HelpingHands Library

The HelpingHands library provides various modules for different "every-day" functionalities. This README file provides an overview of the modules and their functionalities.

## Modules

### utility

The `utility` module provides various utility functions and submodules.

#### data
- `get_data_dir()`: Returns the directory for storing data.
- `backup_data()`: Backs up data to a specified location.
- `json_save()`: Saves data to a JSON file.
- `json_read()`: Reads data from a JSON file.
- `flatten_data()`: Flattens nested data structures.
- `json_to_df()`: Converts JSON data to a DataFrame.
- `save_dict_to_csv()`: Saves a dictionary to a CSV file.
- `create_df()`: Creates a DataFrame from data.
- `swap_columns()`: Swaps the positions of two columns in a DataFrame.
- `load_from_csv()`: Loads data from a CSV file into a DataFrame.
- `delete_duplicates()`: Deletes duplicate rows from a DataFrame.
- `delete_duplicates_add_keywords()`: Deletes duplicate rows and adds keywords to a DataFrame.
- `map_keywords_to_categories()`: Maps keywords to categories in a DataFrame.
- `find_and_assign_tags()`: Finds and assigns tags to data in a DataFrame.
- `add_relevant_tags()`: Adds relevant tags to data in a DataFrame.
- `replace_values()`: Replaces values in a DataFrame.
- `contains_gmaps()`: Checks if a DataFrame contains Google Maps data.
- `manipulate_csv_data()`: Manipulates data in a CSV file.
- `insert_newlines()`: Inserts newlines into text.
- `append_to_or_create_txt_file()`: Appends to or creates a text file.
- `open_txt_file()`: Opens a text file.

#### settings
- `load_settings()`: Loads settings.
  - The function takes parameters to define paths for loading settings, secrets keys, and other environmental settings.

#### logger
- `config_logger()`: Configures the logger.
  - The function accepts multiple parameters that define logger characteristics such as log levels, formats, and file names. Sensible default values are provided for most parameters.

#### tokenbucket
- `TokenBucket`: Implements a token bucket algorithm.

#### decorator
- `retry`: A decorator for retrying functions.
- `time_execution`: Times the execution of a function.

#### helper
- `get_git_tree()`: Retrieves the Git tree of a repository.
- `colorize()`: Adds color to text.
- `get_variable_name()`: Gets the name of a variable as a string.
- `ensure_windows_os()`: Ensures the OS is Windows.

#### web (Note: may be disabled due to missing dependencies)
- `WebConfig`, `setup_browser`, `get_website`, `setup_proxy_simple`, `setup_proxy_wire`, `test_proxy`, `get_original_ip`, `get_current_ip`, `rotate_ip`, `make_soup`, `connect_to_vpn`, `disconnect_from_vpn`, `check_internet`

### openai

The `openai` module provides functions for working with OpenAI APIs.

#### Functions
- `call_whisper()`: Calls the Whisper API.
- `call_gpt()`: Calls the GPT API.
- `gpt_loop()`: Loops the GPT API call.
- `generate_image()`: Generates an image using the DALLE model.
- `dallee_loop()`: Loops the DALLE model image generation.

### audio (Note: may be disabled due to missing dependencies)

The `audio` module provides functions for working with audio files.

#### Functions
- `uhoh()`, `criterr()`, `warning()`, `success()`: Play sounds.
- `ogg_to_mp3()`: Converts OGG audio files to MP3 format.
- `AudioRecorder`: Class for recording audio.

---

## Installation

To install the HelpingHands library, you can use pip:

`pip install helpinghands`

## Usage

Here's an example of how to use the HelpingHands library:

```python
from helpinghands.utility.logger import config_logger

logger = config_logger()

from helpinghands.audio import sounds
from helpinghands.utility.decorator import retry
from helpinghands.openai import call_whisper

@retry
def func(api_key, action, mp3_path):
    try:
        output = call_whisper(api_key, action, mp3_path)
    except:
        sounds.uhoh()
    return output
```

## License
This project serves as a demonstration of and it is not intended for cloning or external contributions. We kindly ask that you respect this intention by not using it for commercial purposes or distributing it. This work is licensed under the [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License](https://creativecommons.org/licenses/by-nc-nd/4.0/)

## Author
[Emil Rühmland](https://github.com/emilrueh)