from ..utility.logger import get_logger

logger = get_logger()

from ..utility.helper import log_exception
from ..utility.data import backup_df

from super_image import ImageLoader
from super_image import DrlnModel, MsrnModel, EdsrModel
from PIL import Image
import requests
import gc

import pandas as pd

import os


def super_image(
    input_file: str,
    scale: int = 2,
    model: str = "edsr-base",
    output_file_name: str = f"scaled",
    output_file_format: str = ".png",
    output_file_dir: str = "./",
    save_comparison: bool = False,
):
    try:
        if input_file.startswith("http"):
            image = Image.open(requests.get(input_file, stream=True).raw)
        else:
            image = Image.open(input_file)

        model_path = f"eugenesiow/{model}"

        if model == "msrn":
            model = MsrnModel.from_pretrained(model_path, scale=scale)
        elif model == "drln-bam":
            model = DrlnModel.from_pretrained(model_path, scale=scale)
        elif model == "edsr-base":
            model = EdsrModel.from_pretrained(model_path, scale=scale)
        else:
            raise ValueError(f"Model {model} not found. Please select another model.")

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
        inputs = None
        preds = None
        # Explicitly delete large objects to free up memory
        del model, inputs, preds, image
        # Manually trigger garbage collection
        gc.collect()


def super_image_loop(
    data,
    input_column,
    scale=2,
    model="edsr-base",
    output_file_name="upscale",
    output_file_format=".png",
    output_file_dir=None,
    save_comparison=False,
):
    if output_file_dir is None:
        output_file_dir = os.getcwd()

    backup_file = os.path.join(output_file_dir, "output_backup_upscale.csv")

    original_type = type(data)
    if isinstance(data, pd.DataFrame):
        data = data.to_dict(orient="records")

    for i, row in enumerate(data):
        input_file = row[input_column]

        full_file_path = os.path.join(
            output_file_dir, f"{output_file_name}_{i}{scale}x{output_file_format}"
        )

        super_image(
            input_file=input_file,
            scale=scale,
            model=model,
            output_file_name=output_file_name,
            output_file_format=output_file_format,
            output_file_dir=output_file_dir,
            save_comparison=save_comparison,
        )

        row[input_column] = full_file_path
        logger.info(f"Processed image for row {i}")

        # Save DataFrame every 100 rows
        if i % 100 == 0:
            backup_df(data, backup_file, i, "UPSCALE", original_type)

    # Save the last batch
    backup_file_final = (
        backup_file.rsplit(".", 1)[0]
        + "_UPSCALE_Final."
        + backup_file.rsplit(".", 1)[1]
    )

    data_final = (
        pd.DataFrame.from_records(data)
        if original_type is pd.DataFrame
        else pd.DataFrame(data)
    )

    data_final.to_csv(backup_file_final, index=False)
    logger.info(f"Final file saved at path: {backup_file_final}")

    # Convert back to DataFrame before returning
    if original_type is pd.DataFrame:
        data = pd.DataFrame.from_records(data)

    return data
