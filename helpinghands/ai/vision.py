from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

# https://platform.openai.com/docs/guides/vision

# ---

from PIL import Image
import base64
from io import BytesIO

import requests


def image_path_to_base64str(image_source, file_type="JPEG"):
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
            image.save(buffered, format=file_type.upper())
            image_bytes = buffered.getvalue()
            base64_encoded = base64.b64encode(image_bytes).decode("utf-8")
            return f"data:image/{file_type.lower()};base64,{base64_encoded}"
    except Exception as e:
        print(f"Error converting image: {e}")
        return None


# ---

# DALL-E 3


def generate_image(prompt):
    response = client.images.generate(
        model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1
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
    print("messages:\n", messages)

    for img in images_in_base64str:
        messages[0]["content"].append(
            {
                "type": "image_url",
                "image_url": {"url": img},
            },
        )

    print("messages:\n", len(messages[0].items()))
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=messages,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


# ---

"""
Things wrong:

    - the output images need to be saved to files
        - in the function or outside?

    - the image_generated need to be base64string from url
        - download and transform (in the function or outside?)
"""

# def image_generation_iteration(image: str, iterations: int = 3, directory: str = None):
#     image_generated = None
#     prompt_generate = None

#     if

#     for i in range(iterations):
#         if not image_generated:
#             # original image
#             original_image_b64str = vision.image_path_to_base64str(image)
#             initial_prompt = f"Your task is to write a highly detailed description of the picture. Make the reader feel like being there."

#             # setting which prompt to use
#             recurring_prompt = f"I have written a prompt for the AI art generation model Dalle 3 to replicate the original image. Your task is to fine tune the prompt to match the original image as closely as possible. Only respond with the new prompt."
#             recurring_prompt = (
#                 recurring_prompt + f"Here is the original prompt: {prompt_generate}"
#                 if not image_generated
#                 else recurring_prompt
#             )
#             # use initial prompt for the first iteration
#             prompt_for_view_image = (
#                 recurring_prompt if image_generated else initial_prompt
#             )
#             images_to_analyze = [original_image_b64str, image_generated_url]
#             # analyze image
#             prompt_generate = vision.view_image(images_to_analyze
#                 , prompt_for_view_image
#             )

#             # generate image
#             image_generated_url = vision.generate_image(prompt_generate)


#             return image_generated_url
