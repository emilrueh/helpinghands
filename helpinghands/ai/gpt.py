from ..utility.logger import get_logger
from ..data.various import backup_df

# from ..utility.decorator import retry

import time, os, pandas as pd
import openai

from .setup import init_openai_client

client = init_openai_client()


# updated calling
def chat(prompt, instructions, model="gpt-3.5-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


# ---


# @retry(
#     (
#         openai.error.RateLimitError,
#         requests.exceptions.ConnectionError,
#         openai.error.APIError,
#         openai.error.ServiceUnavailableError,
#         openai.error.APIConnectionError,
#         requests.exceptions.ReadTimeout,
#         openai.error.Timeout,
#     ),
#     "simple",
# )
def call_gpt(api_key, gpt_model=3, prompt="How are you?", input_text="", timeout=30):
    logger = get_logger()
    if api_key:
        # Set your OpenAI API key
        openai.api_key = api_key
    else:
        return "No OpenAI API key..."

    if gpt_model == 3:
        gpt_model = "3.5-turbo"
    if isinstance(gpt_model, int):
        gpt_model = str(gpt_model)

    # Concatenate the prompt and input input_text
    full_prompt = prompt + str(input_text)

    # Send the request to the OpenAI API
    logger.info(f"Calling GPT-{gpt_model}...")
    response = openai.ChatCompletion.create(
        model=f"gpt-{gpt_model}",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": full_prompt},
        ],
        request_timeout=timeout,
    )
    logger.debug(f"API response: {response}")

    # Extract the generated summary from the API response
    output_text = response.choices[0].message.content

    # print(f"\n{output_text}")

    # Remove non-ASCII characters from the output_text
    output_text = output_text.encode("ascii", "ignore").decode()

    return output_text


def gpt_loop(
    api_key,
    prompt,
    data,
    column_for_input,
    column_for_output,
    gpt_model=3,
    char_max=None,
    char_min=None,
    to_remove=None,
    max_attempts=4,
    tolerance_pct=5,
    output_file_name="gpt",
    output_file_directory=None,
):
    logger = get_logger()
    tolerance = tolerance_pct / 100

    if char_max is not None and char_min is None:
        char_min = int(0.4 * char_max)

    # Convert data to a uniform format (list of dictionaries)
    original_type = type(data)
    if isinstance(data, pd.DataFrame):
        data = data.to_dict(orient="records")
    elif isinstance(data, list):
        data = [{"data": item} for item in data]

    for i, row in enumerate(data):
        attempts = 0
        best_output = None
        best_output_length = float("inf")

        while attempts < max_attempts:
            api_output = call_gpt(
                api_key, gpt_model, prompt, row[column_for_input]
            )  # CALL
            time.sleep(1)
            attempts += 1

            # Handle the case when api_output is None
            if api_output is None or api_output == "":
                logger.error(f"API output is 'None' at row {i}")
                break

            if abs(len(api_output) - char_max) < abs(best_output_length - char_max):
                best_output = api_output
                best_output_length = len(api_output)

            if (
                (char_min * (1 - tolerance))
                <= len(api_output)
                <= (char_max * (1 + tolerance))
            ):
                break

            logger.debug(
                f"Output length not within limits {round(char_min * (1 - tolerance))} and {round(char_max * (1 + tolerance))} with {len(api_output)} characters at row {i}. Trying again with attempt {attempts}..."
            )
            time.sleep(0.5)

        if to_remove is not None:
            for string in to_remove:
                best_output = best_output.replace(string, "")

        row[column_for_output] = best_output
        logger.info(f"Entry: {i + 1} | Index: {i}\n{row[column_for_output]}")

        # Save DataFrame every 100 rows
        if output_file_directory is not None:
            backup_file = os.path.join(
                output_file_directory, f"output_backup_{output_file_name}.csv"
            )
            if i % 100 == 0:
                backup_df(data, backup_file, i, output_file_name.upper(), original_type)

    # Save the last batch which might contain less than 100 rows
    if backup_file is not None:
        backup_file_final = (
            backup_file.rsplit(".", 1)[0]
            + f"_{output_file_name.upper()}_Final."
            + backup_file.rsplit(".", 1)[1]
        )

        # Convert back to DataFrame if necessary
        if isinstance(data, list):
            data = pd.DataFrame(data)

        data.to_csv(backup_file_final, index=False)
        logger.info(f"Final file saved at path: {backup_file_final}")

    return data
