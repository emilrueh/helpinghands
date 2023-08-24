from ..utility.logger import get_logger

logger = get_logger()

from ..utility.helper import log_exception
from ..utility.data import backup_df, get_image, get_image_size

from super_image import ImageLoader
from super_image import DrlnModel, MsrnModel, EdsrModel
from PIL import Image
import requests
import gc

import pandas as pd
import time

import os


def load_model(model_name: str, scale: int = 2):
    model_path = f"eugenesiow/{model_name}"

    if model_name == "msrn":
        return MsrnModel.from_pretrained(model_path, scale=scale)
    elif model_name == "drln-bam":
        return DrlnModel.from_pretrained(model_path, scale=scale)
    elif model_name == "edsr-base":
        return EdsrModel.from_pretrained(model_path, scale=scale)
    else:
        raise ValueError(
            f"Model {model_name} not found. Please select another model_name."
        )


def super_image(
    input_file: str,
    scale: int = 2,
    max_sqr_x: int = 1000,  # this is the height and lenght of a square
    model_name: str = "edsr-base",
    output_file_name: str = "scaled",
    output_file_format: str = ".png",
    output_file_dir: str = "./",
    save_comparison: bool = False,
    model=None,
    delete_model=True,
):
    max_res = max_sqr_x * max_sqr_x

    if input_file:
        image_obj = get_image(input_file)
        width, height = get_image_size(image_obj)

        if width * height >= max_res:
            print(
                f"{width}x{height} is large enough and does not need to be upscaled for this purpose."
            )
            return
        if width * height >= max_res - (max_res // 3):
            scale = 2

    if model is None:
        model = load_model(model_name, scale)

    wait_time = 0.3 if scale <= 2 else 0.5

    try:
        if input_file.startswith("http"):
            image = Image.open(requests.get(input_file, stream=True).raw)
            time.sleep(wait_time)
        else:
            image = Image.open(input_file)

        inputs = ImageLoader.load_image(image)
        preds = model(inputs)

        full_file_path = os.path.join(
            output_file_dir, f"{output_file_name}{scale}x{output_file_format}"
        )

        ImageLoader.save_image(preds, full_file_path)
        if save_comparison:
            ImageLoader.save_compare(
                inputs, preds, full_file_path.replace("x", "x_compare")
            )

    except Exception as e:
        exception_name = log_exception(e)
    finally:
        # time.sleep(wait_time)
        # Explicitly delete large objects to free up memory
        inputs = preds = image = None
        del inputs, preds, image
        if delete_model:
            model = None
            del model
        # Manually trigger garbage collection
        gc.collect()


def super_image_loop(
    data,
    input_column,
    scale=2,
    model_name="edsr-base",
    output_file_name="upscale",
    output_file_format=".png",
    output_file_dir=None,
    save_comparison=False,
    max_sqr_x=1000,
):
    model = load_model(model_name, scale)

    original_type = type(data)
    if isinstance(data, pd.DataFrame):
        data = data.to_dict(orient="records")

    for i, row in enumerate(data):
        input_file = row[input_column]

        unique_output_file_name = f"{output_file_name}_{i}"
        full_file_path = os.path.join(
            output_file_dir, f"{unique_output_file_name}{scale}x{output_file_format}"
        )

        super_image(
            input_file=input_file,
            scale=scale,
            max_sqr_x=max_sqr_x,
            model_name=model_name,
            output_file_name=unique_output_file_name,
            output_file_format=output_file_format,
            output_file_dir=output_file_dir,
            save_comparison=save_comparison,
            model=model,
            delete_model=False,
        )

        row[input_column] = full_file_path
        logger.info(f"Processed image for row {i}")

        backup_file = None
        # Save DataFrame every 100 rows
        if output_file_dir is not None:
            backup_file = os.path.join(output_file_dir, "output_backup_upscale.csv")
            if i % 100 == 0:
                backup_df(data, backup_file, i, "UPSCALE", original_type)

    # cleaning model after last iteration
    model = None
    del model
    gc.collect()

    data_final = (
        pd.DataFrame.from_records(data)
        if original_type is pd.DataFrame
        else pd.DataFrame(data)
    )

    # Save the last batch
    if backup_file and output_file_dir is not None:
        backup_file_final = (
            backup_file.rsplit(".", 1)[0]
            + "_UPSCALE_Final."
            + backup_file.rsplit(".", 1)[1]
        )
        data_final.to_csv(backup_file_final, index=False)
        logger.info(f"Final file saved at path: {backup_file_final}")

    # Convert back to DataFrame before returning
    if original_type is pd.DataFrame:
        data = pd.DataFrame.from_records(data)

    return data
