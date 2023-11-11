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


# ---
