import logging
from ..utility.logger import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

import requests
import pandas as pd
import os


def generate_image(
    api_key,
    prompt,
    number=1,
    size="1024x1024",
    file_name=None,
    file_extension=".png",
    file_directory=None,
):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    generation_url = "https://api.openai.com/v1/images/generations"
    data = {
        "prompt": prompt[:1000],
        "n": number,
        "size": size,
    }
    response = requests.post(generation_url, headers=headers, json=data)
    response_json = response.json()

    if response.status_code != 200 or "data" not in response_json:
        if (
            "error" in response_json
            and response_json["error"]["code"] == "content_policy_violation"
        ):
            logger.error(f"Content policy violation with prompt: {prompt}")
        else:
            logger.error(f"Request rejected: {response.text}")
        return ["No image generated"]
    elif response.status_code == 200:
        logger.info(f"Successful request with prompt: {prompt}")

    image_urls = [data["url"] for data in response_json["data"]]

    if file_name:
        # If no file_directory is specified, use the current working file_directory
        if file_directory is None:
            file_directory = os.getcwd()

        local_file_paths = []  # Store the local paths of the images
        for i, image_url in enumerate(image_urls):
            image_response = requests.get(image_url)
            file_path = os.path.join(file_directory, f"{file_name}_{i}{file_extension}")
            with open(file_path, "wb") as f:
                f.write(image_response.content)
                logger.info(f"Image saved at {file_path}")

            local_file_paths.append(file_path)

        return local_file_paths  # Return local file paths if images are saved locally

    return image_urls


def dallee_loop(
    api_key,
    data,
    columns_for_input,
    column_for_output,
    num_images=1,
    image_size="1024x1024",
    file_name=None,
    file_extension=".png",
    file_directory=None,
):
    # If file_directory is not specified, set it to the current file_directory
    if file_directory is None:
        file_directory = os.getcwd()

    backup_file = os.path.join(file_directory, "output_backup_imgs.csv")

    # Convert data to a uniform format (list of dictionaries)
    original_type = type(data)
    if isinstance(data, pd.DataFrame):
        data = data.to_dict(orient="records")
    elif isinstance(data, list):
        data = [{"data": item} for item in data]

    for i, row in enumerate(data):
        # Skip if output column already contains a value
        if not (
            pd.isnull(row.get(column_for_output))
            or row.get(column_for_output) == ""
            or str(row.get(column_for_output)).strip() == ""
        ):
            logger.debug(f"Skipping row {row} as it already contains photo")
            continue

        # Concatenate input columns to form the prompt
        prompt = " ".join(str(row[col]) for col in columns_for_input)

        image_urls_or_filepaths = generate_image(
            api_key,
            prompt,
            num_images,
            image_size,
            file_name=f"{file_name}_{i}" if file_name else None,
            file_extension=file_extension,
            file_directory=file_directory,
        )

        row[column_for_output] = image_urls_or_filepaths[0]
        logger.info(f"Event: {i + 1} | Index: {i}\n{row[column_for_output]}")

        # Save DataFrame every 100 rows
        if i % 100 == 0:
            backup_file_temp = (
                backup_file.rsplit(".", 1)[0]
                + f"_IMG_{i//100}."
                + backup_file.rsplit(".", 1)[1]
            )

            # Convert back to DataFrame if necessary
            if original_type is list:
                data_temp = pd.DataFrame(data[: i + 1])
            elif original_type is pd.DataFrame:
                data_temp = pd.DataFrame.from_records(data[: i + 1])

            data_temp.to_csv(backup_file_temp, index=False)
            logger.info(f"File saved at path: {backup_file_temp} until row {i}")

    # Save the last batch which might contain less than 100 rows
    backup_file_final = (
        backup_file.rsplit(".", 1)[0] + "_IMG_Final." + backup_file.rsplit(".", 1)[1]
    )

    # Convert back to DataFrame if necessary
    if original_type is list:
        data_final = pd.DataFrame(data)
    elif original_type is pd.DataFrame:
        data_final = pd.DataFrame.from_records(data)

    data_final.to_csv(backup_file_final, index=False)
    logger.info(f"Final file saved at path: {backup_file_final}")

    # Convert back to DataFrame before returning
    if original_type is pd.DataFrame:
        data = pd.DataFrame.from_records(data)

    return data
