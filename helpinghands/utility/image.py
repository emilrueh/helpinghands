from ..utility.logger import get_logger
from ..utility.helper import log_exception
from ..utility.decorator import retry

import os, requests
import uuid
from urllib.parse import urlparse
from base64 import b64decode
import base64

from io import BytesIO
from PIL import Image

from requests.exceptions import ConnectionError, Timeout
from PIL import UnidentifiedImageError


def convert_byte_sizes(size_in_bytes, unit="KB"):
    if unit == "KB":
        return size_in_bytes / 1024
    elif unit == "MB":
        return size_in_bytes / (1024 * 1024)
    return size_in_bytes


# IMAGE
def get_image_res(image_obj):
    width, height = image_obj.size
    print(f"Image resolution: {width}px x {height}px\n{image_obj}")
    return width, height


@retry((ConnectionError, Timeout, UnidentifiedImageError), "simple")
def get_image(source):
    """
    Accepts: path, url, base64, bytes
    """
    img_obj = None  # Default
    img_format = None  # Default

    if isinstance(source, bytes):
        img_obj = Image.open(BytesIO(source))
        img_format = img_obj.format
    elif bool(urlparse(source).netloc):
        response = requests.get(source)
        img_obj = Image.open(BytesIO(response.content))
        img_format = img_obj.format
    elif source.startswith("data:image"):
        image_data = b64decode(source.split(",")[1])
        img_obj = Image.open(BytesIO(image_data))
        img_format = img_obj.format
    elif os.path.exists(source):
        img_obj = Image.open(source)
        img_format = source.split(".")[-1].upper()
    else:
        raise ValueError("Invalid source.")

    if img_format.upper() == "JPG":
        img_format = "JPEG"

    # logger.debug(f"img_obj = {img_obj}\nimg_format = {img_format}")
    return img_obj, img_format


def image_to_bytes(image_source, file_type="JPEG"):
    try:
        img, img_format = get_image(image_source)

        if img_format.upper() != file_type:
            img_format = file_type

        if img.mode == "P":
            img = img.convert("RGBA")
        with BytesIO() as output:
            img.convert("RGB").save(output, img_format)
            output.seek(0)
            return {"image_bytes": output.read(), "image_format": img_format}

    except Exception as e:
        log_exception(e, verbose=True)
        return {"image_bytes": None, "image_format": None}


def bytes_to_base64(image_bytes, file_type="JPEG"):
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    base64_string = f"data:image/{file_type.lower()};base64,{base64_image}"
    return base64_string


def image_to_base64str(image_source, file_type="JPEG"):
    dict_with_bytes = image_to_bytes(image_source, file_type)
    base64_string = bytes_to_base64(
        dict_with_bytes["image_bytes"], dict_with_bytes["image_format"]
    )
    return base64_string


def get_file_size(source, unit="KB"):
    size = 0

    if isinstance(source, bytes):
        size = len(source)
    elif source.startswith("data:image"):
        size = len(b64decode(source.split(",")[1]))
    elif os.path.exists(source):
        size = os.path.getsize(source)
    elif bool(urlparse(source).netloc):
        response = requests.head(source)
        if "content-length" in response.headers:
            size = int(response.headers.get("content-length", 0))
        else:
            return 0  # content-length header not available
    return convert_byte_sizes(size, unit)


def compress_image(source, output_dir=None, quality=80, unit="KB"):
    logger = get_logger()

    is_bytes = isinstance(source, dict)  # dict as image_to_bytes returns in dict
    is_base64 = isinstance(source, str) and source.startswith("data:image")
    path_exists = os.path.exists(source) if not is_bytes else False

    if is_bytes:
        img_obj = Image.open(BytesIO(source["image_bytes"]))
        img_format = source["image_format"]
        source = source["image_bytes"]
        original_size = convert_byte_sizes(len(source), unit)
    elif is_base64:
        image_data = b64decode(source.split(",")[1])
        img_obj = Image.open(BytesIO(image_data))
        img_format = img_obj.format
        original_size = len(image_data)
    else:
        img_obj, img_format = get_image(source)
        original_size = get_file_size(source, unit)

    with BytesIO() as output:
        img_obj.save(output, format=img_format, quality=quality)
        compressed_data = output.getvalue()

    compressed_size = get_file_size(compressed_data, unit)

    if compressed_size >= original_size:
        logger.info(
            f"Didn't compress as the original img size is smaller than or equal to the compressed size. ({round(original_size, 2)} {unit} -> {round(compressed_size, 2)} {unit})"
        )
        return img_obj

    reduction_percent = ((original_size - compressed_size) / original_size) * 100

    logger.info(
        f"Compressed: {round(original_size, 2)} {unit} -> {round(compressed_size, 2)} {unit} (-{round(reduction_percent, 2)}%)"
    )

    if output_dir and not is_base64 and not is_bytes:
        # creating output_path
        if path_exists:
            input_filename = os.path.basename(source)
            input_name, input_ext = os.path.splitext(input_filename)
        else:
            input_name = str(uuid.uuid4())[:8]
            input_ext = f".{img_format.lower()}" if img_format else ".jpeg"

        index = 0
        while True:
            output_filename = (
                f"{input_name}_comp-{quality}{f'_{index}' if index else ''}{input_ext}"
            )
            output_path = os.path.join(output_dir, output_filename)
            if not os.path.exists(output_path):
                break
            index += 1

        with open(output_path, "wb") as f:
            f.write(compressed_data)
        return output_path
    else:
        return compressed_data
