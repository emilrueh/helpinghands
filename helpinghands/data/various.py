from ..utility.logger import get_logger

import pandas as pd
import json, re, os, random, glob

from pathlib import Path
from collections import Counter


# general data work
def get_data_dir(base_path: str = None):
    """
    Returns the path to the 'data' directory.
    If the directory doesn't exist, it is created.
    """
    if base_path is None:
        base_path = Path().resolve()

    data_dir = base_path / "data"
    data_dir.mkdir(exist_ok=True)

    return data_dir


def add_random_files(df, column_name, file_dir):
    files = os.listdir(file_dir)
    mask = df[column_name].isna() | (df[column_name] == "NaN")

    for idx in df[mask].index:
        random_file = random.choice(files)
        full_path = os.path.join(file_dir, random_file)
        df.at[idx, column_name] = full_path

    return df


def choose_random_file(directory):
    # listing all files in beats dir
    file_paths = [
        f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))
    ]
    # choosing random music file from dir
    random_file_path = os.path.join(directory, random.choice(file_paths))

    return random_file_path


def clean_directory(
    dir_path, file_extensions=["*.csv", "*.json", "*.jpg", "*.jpeg", "*.png"]
):
    logger = get_logger()

    counts = {}
    for ext in file_extensions:
        files_to_delete = glob.glob(os.path.join(dir_path, ext))
        if not files_to_delete:
            continue

        counts[ext] = len(files_to_delete)

        for file in files_to_delete:
            try:
                os.remove(file)
            except PermissionError:
                logger.warning(f"Permission denied: Couldn't delete {file}")

    logger.info(f"Deleted {counts} files in {os.path.basename(dir_path)}")


# STRING
def remove_duplicate_words(input_string):
    counts = Counter(input_string.lower().split())
    words = input_string.split()
    result = []
    for word in words:
        if counts[word.lower()] > 1:
            counts[word.lower()] -= 1
        else:
            result.append(word)
    return " ".join(result)


# NUMBERS
def extract_number(price):
    if price is None or price.lower() == "nan":
        return None
    elif price.lower() == "free":
        return 0
    # Find all groups of digits in the string, potentially separated by a comma or a dot
    number_parts = re.findall(r"(\d+[\.,]\d+|\d+)", price)
    if not number_parts:
        return None
    # Replace any commas in the number with a dot, convert to float
    number = float(number_parts[0].replace(",", "."))
    # Round to the nearest integer
    rounded_number = round(number)
    return rounded_number


# DF, CSV, JSON


# JSON
def json_save(data, filename, append=False):
    # If appending, load existing data and update it
    if append and os.path.exists(filename):
        with open(filename, "r") as file:
            existing_data = set(json.load(file))
        existing_data.update(data)
        data = list(existing_data)

    # Save the data
    with open(filename, "w") as file:
        json.dump(data, file)


def json_read(json_filename):
    # Specify the filename of the JSON backup file
    # Load JSON data from the file
    with open(json_filename, "r") as file:
        json_data = file.read()

    # Convert the JSON data back into the dictionary
    json_dict = json.loads(json_data)

    return json_dict


def json_to_df(file_path):
    # Load JSON data from file
    with open(file_path) as file:
        data = json.load(file)

    try:
        # Try to normalize the JSON data (i.e., handle nested structure)
        df = pd.json_normalize(data)
    except:
        # If an error is raised, assume the JSON data isn't nested
        df = pd.DataFrame(data)

    return df


def create_df(data):
    return pd.DataFrame(data)


def df_from_csv(filename):
    df = pd.read_csv(filename)
    return df


def backup_df(data, path, i, prefix, original_type):
    logger = get_logger()
    backup_file_temp = (
        path.rsplit(".", 1)[0] + f"_{prefix}_{i//100}." + path.rsplit(".", 1)[1]
    )

    data_temp = (
        pd.DataFrame.from_records(data[: i + 1])
        if original_type is pd.DataFrame
        else pd.DataFrame(data[: i + 1])
    )

    data_temp.to_csv(backup_file_temp, index=False)
    logger.info(f"File saved at path: {backup_file_temp} until row {i}")
