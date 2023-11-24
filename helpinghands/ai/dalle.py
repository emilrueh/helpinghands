from ..utility.logger import get_logger
from ..utility.data import backup_df

import requests
import pandas as pd
import os, time


class ContentPolicyViolationError(Exception):
    pass


from .assistant import init_openai_client

client = init_openai_client()


# DALL-E 3
def generate_image(prompt, size="1024x1024", amount=1, ai_model="dall-e-3"):
    response = client.images.generate(
        model=ai_model, prompt=prompt, size=size, quality="standard", n=amount
    )
    return response.data[0].url


# deprecated
# DALL-E 2
def generate_image(
    api_key,
    prompt,
    number=1,
    size="1024x1024",
    file_name=None,
    file_extension=".png",
    file_directory=None,
):
    logger = get_logger()
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
            raise ContentPolicyViolationError(
                f"Content policy violation with prompt: {prompt}"
            )
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
                logger.debug(f"Image saved at {file_path}")

            local_file_paths.append(file_path)

        return local_file_paths  # Return local file paths if images are saved locally

    return image_urls


def dallee_loop(
    api_key,
    data,
    columns_for_input,
    column_for_output,
    what="event",
    attributes=[
        "intricate detail",
        "high quality",
        "cinematic lighting",
    ],
    num_images=1,
    image_size="1024x1024",
    output_file_name="dallee",
    output_file_extension=".png",
    output_file_directory=None,
):
    logger = get_logger()
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
            or str(row.get(column_for_output)).strip().lower() == "nan"
        ):
            logger.debug(f"Skipping row {i} as it already contains photo")
            continue

        # Concatenate input columns to form the prompt
        column_content = " ".join(str(row[col]) for col in columns_for_input)
        arg_content = f'{what}, {", ".join(attributes)}'
        prompt = f"{column_content} {arg_content}"

        attempt = 0
        while attempt < 2:
            try:
                image_urls_or_filepaths = generate_image(
                    api_key,
                    prompt,
                    num_images,
                    image_size,
                    file_name=f"{output_file_name}_{i}" if output_file_name else None,
                    file_extension=output_file_extension,
                    file_directory=output_file_directory,
                )
                break
            except ContentPolicyViolationError:
                prompt = arg_content
            finally:
                time.sleep(1)
                attempt += 1

        row[column_for_output] = image_urls_or_filepaths[0]
        logger.info(f"Event: {i + 1} | Index: {i}\n{row[column_for_output]}")

        backup_file = None
        # Save DataFrame every 100 rows
        if output_file_directory is not None:
            backup_file = os.path.join(
                output_file_directory, f"output_backup_{output_file_name}.csv"
            )
            if i % 100 == 0:
                backup_df(data, backup_file, i, output_file_name.upper(), original_type)

    # Convert back to DataFrame if necessary
    if original_type is list:
        data_final = pd.DataFrame(data)
    elif original_type is pd.DataFrame:
        data_final = pd.DataFrame.from_records(data)

    # Save the last batch which might contain less than 100 rows
    if backup_file and output_file_directory is not None:
        backup_file_final = (
            backup_file.rsplit(".", 1)[0] + "_Final." + backup_file.rsplit(".", 1)[1]
        )
        data_final.to_csv(backup_file_final, index=False)
        logger.info(f"Final file saved at path: {backup_file_final}")

    # Convert back to DataFrame before returning
    if original_type is pd.DataFrame:
        data = pd.DataFrame.from_records(data)

    return data
