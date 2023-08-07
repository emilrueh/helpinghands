# HelpingHands Library

The HelpingHands library provides various modules for different "every-day" functionalities. This README file provides an overview of the modules and their functionalities.

## Modules

### audio

The `audio` module provides functions for working with audio files.

#### Functions

- `uhoh()`: Plays the "uhoh" sound.
- `criterr()`: Plays the "criterr" sound.
- `warning()`: Plays the "warning" sound.
- `success()`: Plays the "success" sound.
- `ogg_to_mp3()`: Converts OGG audio files to MP3 format.
- `AudioRecorder()`: Class for recording audio.

### openai

The `openai` module provides functions for working with OpenAI APIs.

#### Functions

- `call_whisper()`: Calls the Whisper API.
- `call_gpt()`: Calls the GPT API.
- `gpt_loop()`: Loops the GPT API call.
- `generate_image()`: Generates an image using the DALLE model.
- `dallee_loop()`: Loops the DALLE model image generation.

### utility

The `utility` module provides various utility functions.

#### Functions

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

### Other Modules

- `settings`: Provides functions for loading settings.
- `logger`: Configures the logger for logging purposes.
- `tokenbucket`: Implements a token bucket algorithm.

### Helper Functions

The `helper` module provides various helper functions.

- `get_git_tree()`: Retrieves the Git tree of a repository.
- `setup_browser()`: Sets up a web browser for automation.
- `make_soup()`: Creates a BeautifulSoup object from HTML.
- `colorize()`: Adds color to text.
- `get_variable_name()`: Gets the name of a variable as a string.
- `check_internet()`: Checks internet connectivity.
- `connect_to_vpn()`: Connects to a VPN.
- `disconnect_from_vpn()`: Disconnects from a VPN.

## Installation

To install the HelpingHands library, you can use pip:

`pip install helpinghands`


## Usage

Here's an example of how to use the HelpingHands library:

```python
from helpinghands.utility.logger import config_logger

logger = config_logger()

from helpinghands.audio import sounds, 
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

---
## License
    This project serves as a demonstration of and it is not intended for cloning or external contributions. We kindly ask that you respect this intention by not using it for commercial purposes or distributing it.

    This work is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License. This means that while you are welcome to view and understand the code, it is not meant to be repurposed under standard open-source protocols.

    To view a copy of this license, please visit http://creativecommons.org/licenses/by-nc-nd/4.0/ or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.

    The terms of this license stipulate that:

    Attribution - If sharing the material, you must give appropriate credit and provide a link to the license.
    NonCommercial - The material may not be used for commercial purposes.
    NoDerivatives - If you remix, transform, or build upon the material, you may not distribute the modified material.
