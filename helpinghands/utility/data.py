from ..utility.logger import get_logger

logger = get_logger()

import pandas as pd
import json
import tempfile
import shutil
import os
from pathlib import Path
import uuid
import numpy as np
from langdetect import detect
from collections import Counter
import re
import textwrap
from termcolor import colored
import platform, subprocess


# general data work
def get_data_dir(base_path: str = None):
    """
    Returns the path to the 'data' directory.
    If the directory doesn't exist, it is created.
    """
    if base_path is None:
        base_path = Path().resolve()

    data_dir = base_path / "data"
    # data_dir.mkdir(exist_ok=True)

    return data_dir


def backup_data(input_data, backup_directory, input_name=None):
    # Convert backup_directory to a Path object
    backup_directory = Path(backup_directory)
    # Create backup_directory if it doesn't exist
    backup_directory.mkdir(parents=True, exist_ok=True)

    # Determine the file extension
    if isinstance(input_data, pd.DataFrame):
        file_extension = ".csv"
    elif isinstance(input_data, str) and input_data.endswith((".csv", ".txt", ".json")):
        file_extension = os.path.splitext(input_data)[1]
    elif isinstance(input_data, dict) or (
        isinstance(input_data, str) and input_data.endswith(".json")
    ):
        file_extension = ".json"
    elif isinstance(input_data, str):
        file_extension = ".txt"
    else:
        raise ValueError("Unsupported data type")

    # Create a temporary file with the desired file name
    with tempfile.NamedTemporaryFile(
        suffix=file_extension, delete=False, mode="w"
    ) as temp_file:
        # Save the input data to the temporary file
        if isinstance(input_data, pd.DataFrame):
            input_data.to_csv(temp_file.name, index=False)
        elif isinstance(input_data, str) and input_data.endswith(
            (".csv", ".txt", ".json")
        ):
            with open(input_data, "r") as data_file:
                temp_file.write(data_file.read())
        elif isinstance(input_data, dict):
            json.dump(input_data, temp_file)
        elif isinstance(input_data, str) and input_data.endswith(".json"):
            with open(input_data, "r") as data_file:
                json_data = json.load(data_file)
            with open(temp_file.name, "w") as temp_json_file:
                json.dump(json_data, temp_json_file)
        elif isinstance(input_data, str):
            temp_file.write(input_data.encode("utf-8"))

        # Determine the backup file name
        if input_name is not None:
            backup_file_name = f"{input_name}_backup{file_extension}"
        else:
            backup_file_name = f"backup_{uuid.uuid4()}{file_extension}"

        # Copy the temporary file to the backup directory
        backup_file_path = backup_directory / backup_file_name
        shutil.copy(temp_file.name, backup_file_path)

    # Remove the temporary file
    os.unlink(temp_file.name)


def backup_df(data, path, i, prefix, original_type):
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


# @log_func_name
def flatten_data(data):
    flattened_data = []
    for keyword in data:
        for item in data[keyword]:
            if data[keyword][item] is not None:
                temp_dict = data[keyword][item].copy()  # get the details by their ID
                flattened_data.append(temp_dict)
    return flattened_data


# DF and CSV
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


def save_dict_to_csv(all_events_dict, csv_filename):
    flattened_data = []

    for keyword, keyword_events_dict in all_events_dict.items():
        for event_id, event_info in keyword_events_dict.items():
            if event_info is not None:  # if event_info is None, we skip the event
                info_copy = (
                    event_info.copy()
                )  # we don't want to modify the original dict
                info_copy["Keyword"] = keyword
                # info_copy["event_id"] = event_id
                flattened_data.append(info_copy)

    df = pd.DataFrame(flattened_data)
    df.to_csv(
        csv_filename, index=False
    )  # write dataframe to CSV, without the row index


def create_df(data):
    return pd.DataFrame(data)


def swap_columns(df, col1, col2):
    # Create new column order
    column_names = df.columns.tolist()
    i1, i2 = column_names.index(col1), column_names.index(col2)
    column_names[i2], column_names[i1] = column_names[i1], column_names[i2]

    # Reorder dataframe
    df = df[column_names]
    return df


def load_from_csv(filename):
    df = pd.read_csv(filename)
    return df


def delete_duplicates(data, columns_to_compare=None):
    if isinstance(data, str):  # if the input is a file path
        data = pd.read_csv(data)

    # Keep one instance of each event with the same name, remove others
    df_no_duplicates = data.drop_duplicates(subset=columns_to_compare, keep="first")

    return df_no_duplicates  # return the DataFrame object


def delete_duplicates_add_keywords(data, columns_to_compare=None):
    if isinstance(data, str):  # if the input is a file path
        data = pd.read_csv(data)

    original_data = data.copy()  # copy the original data to compare later

    logger.debug(colored(f"DataFrame columns: {data.columns}", "yellow"))
    logger.debug(colored(f"Columns to compare: {columns_to_compare}", "yellow"))

    # Convert 'Keyword' to a set, which removes duplicates within each group
    try:
        data["Keyword"] = data.groupby(columns_to_compare)["Keyword"].transform(
            lambda x: ",".join(set(str(val) for val in x.str.split(",").sum()))
        )
    except TypeError as e:
        for i, val in enumerate(data["Keyword"]):
            try:
                set(str(val).split(","))
            except TypeError:
                logger.error(f"Error at index {i} with value {val}")
                raise e

    # Keep one instance of each event with the same name, remove others
    df_no_duplicates = data.drop_duplicates(subset=columns_to_compare, keep="first")

    # Print the indexes and keywords
    added_keywords_rows = df_no_duplicates[
        df_no_duplicates["Keyword"].str.contains(",", na=False)
    ]
    indexes_and_keywords = added_keywords_rows[["Keyword"]]
    logger.info("Rows that gained keywords:")
    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        logger.debug(indexes_and_keywords)

    logger.info(f"Total rows that gained keywords: {indexes_and_keywords.shape[0]}")

    return df_no_duplicates


def map_keywords_to_categories(keywords, category_dict):
    if pd.isnull(keywords):  # Add this check to handle NaN values (which are floats)
        return ""
    categories = set()  # Change this from a list to a set
    for keyword in keywords.split(","):
        keyword = keyword.strip().upper()  # Ensure format matches keys in dictionary
        if keyword in category_dict:
            category_values = category_dict[keyword]
            if isinstance(category_values, list):  # Check if the value is a list
                for value in category_values:
                    categories.add(value)
            else:
                categories.add(
                    category_values
                )  # Use add method for sets instead of append
    return ",".join(categories)


def find_and_assign_tags(
    df, tags, columns_to_check, output_column, default_value, standalone_tags=None
):
    def find_tags(row):
        row_values = " ".join(str(row[col]) for col in columns_to_check)
        text = row_values.lower()

        found_tags = []  # Initialize found_tags as an empty list
        # This part handles special cases where you need the tag to match the entire word.
        if standalone_tags:
            # Update the regular expression to consider word boundaries properly
            found_tags = [
                tag
                for tag in standalone_tags
                if re.search(rf"(^|\s){tag.lower()}(\s|$)", text)
            ]

        # For other tags, the substring matching is used.
        other_tags = set(tags) - set(standalone_tags)
        found_tags += [tag for tag in other_tags if tag.lower() in text]

        if not found_tags:
            found_tags.append(default_value)
        return ", ".join(found_tags)

    df[output_column] = df.apply(find_tags, axis=1)
    return df


def add_relevant_tags(
    df, column_to_check, column_to_apply, categories_ordered, default=None
):
    categories_ordered_lower = [category.lower() for category in categories_ordered]

    def find_relevant_category(row):
        if pd.isna(row[column_to_check]) or not isinstance(row[column_to_check], str):
            return default

        categories_in_row = [
            category.strip().lower() for category in row[column_to_check].split(",")
        ]

        for category in categories_ordered_lower:
            if category in categories_in_row:
                return category.upper()

        return default

    df[column_to_apply] = df.apply(find_relevant_category, axis=1)
    return df


def replace_values(df, column_to_check, list_of_values, value_to_replace_with):
    def replace_if_contains(row):
        row_value = row[column_to_check]
        if pd.isna(row_value):
            if np.nan in list_of_values:
                return value_to_replace_with
            else:
                return row_value

        if not isinstance(row_value, str):
            return row_value

        if any(
            (val if isinstance(val, str) else str(val)).lower() in row_value.lower()
            for val in list_of_values
        ):
            return value_to_replace_with

        return row_value

    df[column_to_check] = df.apply(replace_if_contains, axis=1)
    return df


def contains_gmaps(link):
    if pd.isna(link):
        return link
    elif "http" not in link:
        return np.nan
    else:
        return link


def manipulate_csv_data(
    file_path=None, output_filepath=None, operations=None, input_df=None
):
    """
    Perform a series of operations on a DataFrame which can be loaded from a CSV file, and save the resulting DataFrame to another CSV file.

    Parameters:
    - file_path (str, optional): Path to the input CSV file. Defaults to None.
    - output_filepath (str, optional): Path to the output CSV file. If None, overwrites the input file. Defaults to None.
    - operations (list, optional): A list of dictionaries specifying the operations to be performed. If None, no operations are performed. Defaults to None.
        - "add_column": Add a new column with a specified value.
        - "remove_column": Remove a specified column.
        - "lowercase", "uppercase", "titlecase": Convert the text in a specified column to the respective case.
        - "split": Split the text in a specified column into a list based on a specified delimiter.
        - "substring": Extract a substring from the text in a specified column based on given start and end indices.
        - "replace_string": Replace a specified old text with a new text in a given column.
        - "filter_out_keywords": Remove rows containing any of a list of specified keywords in any of a list of specified columns.
        - "language_filter": Keep only rows where the text in a specified column is detected to be in any of a list of specified languages.
        - "filter_for_keywords": Keep only rows where the text in any of a list of specified columns (excluding those in another list of specified columns) contains any of a list of specified keywords.
    - input_df (pandas.DataFrame, optional): An input DataFrame to perform operations on. If None, the DataFrame is loaded from file_path. Defaults to None.

    Returns:
    - The resulting DataFrame after performing the specified operations.

    Example:
    >>> operations = [{"action": "add_column", "column_name": "new_col", "column_value": "value"},
                      {"action": "remove_column", "column_name": "remove_col"},
                      {"action": "lowercase", "column_name": "text_col"},
                      {"action": "split", "column_name": "split_col", "delimiter": "-"},
                      {"action": "substring", "column_name": "text_col", "start_index": 0, "end_index": 5},
                      {"action": "replace_string", "column_name": "text_col", "old_text": "old", "new_text": "new"},
                      {"action": "filter_out_keywords", "keywords": ["keyword1", "keyword2"], "columns": ["col1", "col2"]},
                      {"action": "language_filter", "column_name": "text_col", "languages": ["en", "fr"]},
                      {"action": "filter_for_keywords", "keywords": ["keyword1", "keyword2"], "columns": ["col1", "col2"], "skip_columns": ["skip_col"]}]
    >>> manipulate_csv_data(file_path="input.csv", output_filepath="output.csv", operations=operations)
    """

    if file_path is None and input_df is None:
        logger.error("Either a file path or an input DataFrame must be provided.")
        raise ValueError("Either a file path or an input DataFrame must be provided.")
    elif file_path is not None and input_df is not None:
        logger.error("Only one of file path or input DataFrame should be provided.")
        raise ValueError("Only one of file path or input DataFrame should be provided.")

    if input_df is not None:
        df = input_df
    else:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        df = pd.read_csv(file_path)

    # Fill NA/NaN values differently for numeric and non-numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns
    df.loc[:, numeric_cols] = df.loc[:, numeric_cols].fillna(0)
    df.loc[:, non_numeric_cols] = df.loc[:, non_numeric_cols].fillna("")
    if output_filepath == None:
        output_filepath = file_path

    if operations == None:
        logger.warning("No operations specified. Skipping function...")
        return

    # Apply operations
    for operation in operations:
        action = operation["action"]
        column_name = operation.get("column_name")

        if column_name and column_name not in df.columns:
            logger.warning(f"Column '{column_name}' not found in DataFrame.")
            continue

        try:
            if action == "add_column":
                df[operation["column_name"]] = operation["column_value"]
            elif action == "remove_column":
                df.drop(columns=[column_name], axis=1, inplace=True)
            elif action in ["lowercase", "uppercase", "titlecase"]:
                df[column_name] = df[column_name].astype(str)
                if action == "lowercase":
                    df[column_name] = df[column_name].str.lower()
                elif action == "uppercase":
                    df[column_name] = df[column_name].str.upper()
                else:  # titlecase
                    df[column_name] = df[column_name].str.title()
            elif action == "split":
                df[operation["new_column_name"]] = df[column_name].str.split(
                    pat=operation["delimiter"]
                )
            elif action == "substring":
                start_index = operation["start_index"]
                end_index = operation["end_index"]
                new_column_name = operation.get("new_column_name", None)
                if new_column_name:
                    df[new_column_name] = df[column_name].str[start_index:end_index]
                else:
                    df[column_name] = df[column_name].str[start_index:end_index]
            elif action == "replace_string":
                df[column_name] = df[column_name].replace(
                    operation["old_text"], operation["new_text"], regex=True
                )
            elif action == "filter_out_keywords":
                keywords = [keyword.lower() for keyword in operation["keywords"]]
                columns = operation["columns"]
                mask = np.logical_or.reduce(
                    [
                        df[column].str.lower().str.contains(keyword, na=False)
                        for keyword in keywords
                        for column in columns
                    ]
                )
                df = df[~mask]
            elif action == "language_filter":
                languages = operation["languages"]
                column = operation["column_name"]
                mask = df[column].apply(
                    lambda x: detect(x) in languages if x else False
                )
                df = df[mask]
            elif action == "filter_for_keywords":
                columns = operation["columns"]
                keywords = [kw.lower() for kw in operation["keywords"]]
                skip_columns = operation.get("skip_columns", [])
                mask = []
                for index, row in df.iterrows():
                    row_text = " ".join(
                        str(row[column]).lower()
                        for column in columns
                        if column not in skip_columns
                    )
                    if any(keyword in row_text for keyword in keywords):
                        mask.append(True)
                    else:
                        mask.append(False)
                df = df[mask]
            else:
                logger.error(f"Invalid action '{action}'")
                raise ValueError(f"Invalid action '{action}'")

        except Exception as e:
            logger.error(
                f"Error occurred during action '{action}' on column '{column_name}': {e}",
                exc_info=True,
            )
            continue

    try:
        df.to_csv(output_filepath, index=False)
    except Exception as e:
        logger.error(
            f"Error occurred while saving DataFrame to CSV: {e}", exc_info=True
        )

    return df


# TXT
def insert_newlines(string, every=64):
    logger.info(f"Formatted string.")
    return "\n".join(textwrap.wrap(string, every))


def write_to_txt_file(input_text, file_name, output_directory, mode="append"):
    """
    Specify any mode except for 'append' for write and replace.
    """
    output_file_path = os.path.join(output_directory, f"{file_name}.txt")
    with open(output_file_path, "a" if mode == "append" else "w") as f:
        f.write(("\n" if mode == "append" and f.tell() > 0 else "") + input_text)


def load_text_from_file(txt_file_path):
    try:
        with open(txt_file_path, "r") as f:
            return f.read()
    except:
        return print(f"Failed to open .txt file at path: {txt_file_path}")


def open_txt_file(file_path):
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", file_path], check=True)
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", file_path], check=True)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
