from ..utility.logger import get_logger
from ..utility.helper import log_exception
from ..utility.data import backup_df, get_image, get_image_res
from ..utility.decorator import time_execution

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
        raise ValueError(f"Model {model_name} not found. Please select another model_name.")


def super_image(
    input_file: str,
    scale: int = 2,
    max_res: int = 1000,  # squared
    model_name: str = "edsr-base",
    output_file_name: str = "scaled",
    output_file_format: str = "png",
    output_file_dir: str = "./",
    save_comparison: bool = False,
    model=None,
    delete_model=True,
):
    logger = get_logger()
    if not max_res:
        logger.warning(f"Maximum resolution check switched off.")
        max_res = "unset"
    else:
        max_res = max_res * max_res

    if input_file and input_file != "NaN":
        try:
            image_obj, _ = get_image(input_file)
        except ValueError as e:
            log_exception(e)
            return None

        width, height = get_image_res(image_obj)

        if width * height >= max_res:
            logger.debug(
                f"{width}x{height} is large enough and does not need to be upscaled for this purpose as higher than max_res which is {max_res}{'px' if max_res else '.'}"
            )
            return
        if width * height >= max_res * 0.7:
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

        full_file_path = os.path.join(output_file_dir, f"{output_file_name}{scale}x.{output_file_format}")
        ImageLoader.save_image(preds, full_file_path)
        if save_comparison:
            ImageLoader.save_compare(inputs, preds, full_file_path.replace("x", "x_compare"))

        return full_file_path

    except Exception as e:
        exception_name = log_exception(e)
        return None
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


@time_execution(2, "minutes")
def super_image_loop(
    data,
    input_column,
    scale=2,
    model_name="edsr-base",
    output_img_name="upscale",
    output_img_format="png",
    output_files_dir=None,
    save_comparison=False,
    max_res=900,
    sleep=1,
):
    logger = get_logger()
    model = load_model(model_name, scale)
    backup_file = os.path.join(output_files_dir, f"output_backup_{output_img_name.upper()}.csv")
    original_type = type(data)

    for i, row in data.iterrows():
        input_file = row[input_column]
        unique_output_file_name = f"{output_img_name}_{i}"

        upscaled_file = super_image(
            input_file=input_file,
            scale=scale,
            max_res=max_res,
            model_name=model_name,
            output_file_name=unique_output_file_name,
            output_file_format=output_img_format,
            output_file_dir=output_files_dir,
            save_comparison=save_comparison,
            model=model,
            delete_model=False,
        )

        data.at[i, input_column] = upscaled_file if upscaled_file else input_file

        logger.info(f"Row:{i} - {'Upscaled' if upscaled_file else 'Did not upscale'} image:\n{input_file}")
        if sleep:
            time.sleep(sleep)
        # Save DataFrame every 100 rows
        if output_files_dir is not None:
            if i % 100 == 0:
                backup_df(data, backup_file, i, output_img_name.upper(), original_type)

    # cleaning model after last iteration
    model = None
    del model
    gc.collect()

    # Save the last batch
    if backup_file and output_files_dir is not None:
        backup_file_final = backup_file.rsplit(".", 1)[0] + "_Final." + backup_file.rsplit(".", 1)[1]
        data.to_csv(backup_file_final, index=False)
        logger.info(f"Final CSV saved at: {backup_file_final}")

    return data
