from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()

# https://platform.openai.com/docs/guides/vision

# ---

from PIL import Image
import base64
from io import BytesIO

import requests

from ..ai.gpt import chat


def image_to_base64str(image_source, file_type="JPEG"):
    if "http" in image_source or "https" in image_source:
        # Handle URL
        response = requests.get(image_source)
        if response.status_code == 200:
            image_data = BytesIO(response.content)
        else:
            print("Failed to download image.")
            return None
    else:
        # Handle file path
        if "." in file_type:
            file_type = file_type.replace(".", "")
        if file_type == "jpg":
            file_type = "jpeg"
        image_data = image_source

    try:
        with Image.open(image_data) as image:
            buffered = BytesIO()
            # Convert to RGB if necessary
            if image.mode in ("RGBA", "LA") or (
                image.mode == "P" and "transparency" in image.info
            ):
                image = image.convert("RGB")
            image.save(buffered, format=file_type.upper())
            image_bytes = buffered.getvalue()
            base64_encoded = base64.b64encode(image_bytes).decode("utf-8")
            return f"data:image/{file_type.lower()};base64,{base64_encoded}"
    except Exception as e:
        print(f"{type(e).__name__} converting image: {e}")
        return None


def save_b64str_images_to_file(
    images: list, files_directory: str = "./", file_extension: str = None
):
    for i, image in enumerate(images):
        # Decode the base64 string
        image_data = base64.b64decode(image.split(",")[1])

        # Optionally process the image with PIL (e.g., convert format)
        with Image.open(BytesIO(image_data)) as img_obj:
            # get the file extension
            ext = file_extension or img_obj.format.lower()

            buffered = BytesIO()
            img_obj.convert("RGB").save(buffered, format=ext)
            buffered.seek(0)
            output_image_bytes = buffered.read()

        # fmt: off
        # Write the image bytes to a file
        with open(os.path.join(
                files_directory, f"generated_image_{i + 1}.{ext}"
            ), mode="wb") as file:
            file.write(output_image_bytes)


# ---


# DALL-E 3
def generate_image(prompt, size="1024x1024", amount=1, ai_model="dall-e-3"):
    response = client.images.generate(
        model=ai_model, prompt=prompt, size=size, quality="standard", n=amount
    )
    return response.data[0].url


# ---


def view_image(images_in_base64str: list, prompt, max_tokens=300):
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt}],
        },
    ]

    for img in images_in_base64str:
        if img is None:
            continue
        messages[0]["content"].append(
            {
                "type": "image_url",
                "image_url": {"url": img},
            },
        )

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=messages,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def image_generation_iteration(
    image: str,
    iterations: int = 3,
    directory: str = None,
    retry_prompt: str = "Please adjust the following description to avoid getting it flagged due to violations via certain words. {} Here is the prompt: ",
):
    """
    Idea:
        loop:
            - take an image
            - turn it to base64 string

            1 - send to gpt4 to generate description
            2 - let image be generated from gpt4-vision from description

            - save generated image to file
              (seperate function)

            3 - ask gpt what it thinks the percantage difference between
                the two images is and between the prompts and create dataset
                (seperate function)
    """
    image_generated_b64str = None
    prompt_generate = None

    images_b64strings = []
    try:
        # make directory if not exists
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        for i in range(iterations):
            print("\n> Iteration:", i + 1)

            # take an image and transform it to base 64 string
            print("> Transforming original image to base 64 string...")
            original_image_b64str = image_to_base64str(image)

            # setting which prompt to use
            # keep a prompt for the first iteration when no generated image yet
            initial_prompt = f"Your task is to write a highly detailed description of the picture. Make the reader feel like being there."
            recurring_prompt = f"I have written a prompt for the AI art generation model Dalle 3 to replicate the original image. Your task is to fine tune the prompt to match the original image as closely as possible. Only respond with the new prompt."

            # add old prompt only to recurring prompt
            recurring_prompt = (
                recurring_prompt + f"Here is the original prompt: {prompt_generate}"
                if not image_generated_b64str
                else recurring_prompt
            )

            # use initial prompt only for the first iteration
            prompt_for_view_image = (
                recurring_prompt if image_generated_b64str else initial_prompt
            )

            # set images for gpt4 vision to analyze
            images_to_analyze = [
                original_image_b64str,
                image_generated_b64str,
            ]

            # analyze image
            print("> Analyzing image...")
            prompt_generate = view_image(images_to_analyze, prompt_for_view_image)

            retries = 3
            while retries != 0:
                try:
                    # generate image
                    print("> Generating image...")
                    image_generated_url = generate_image(prompt_generate)
                    break
                except Exception as e:
                    image_generated_url = None
                    print(f"{type(e).__name__} - {e}\n> Retrying with new prompt...")
                    prompt_generate = chat(
                        f"{retry_prompt}{prompt_generate} Here it is: ",
                        instructions=" Only respond with the adjusted prompt.",
                    )
                finally:
                    retries -= 1

            if image_generated_url is None:
                print("> No image url available. Exiting...")
                return images_b64strings

            print(f"\nprompt_generate = {prompt_generate}\n")
            print(f"image_generated_url = {image_generated_url}")

            # transorm image to base 64 string
            print("Transforming to base 64 string...")
            image_generated_b64str = image_to_base64str(image_generated_url)

            print(f"image_generated_b64str = {image_generated_b64str}")

            # store images in list
            print("> Storing base 64 strings in list...")
            images_b64strings.append(image_generated_b64str)

            print(f"> Function return (images_b64strings): {images_b64strings}")

    except Exception as e:
        print(f"{type(e).__name__} - {e}\n> Returning...")

    return images_b64strings
