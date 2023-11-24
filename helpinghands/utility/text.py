from ..utility.logger import get_logger

import os, subprocess, textwrap, platform


# TXT
def insert_newlines(string, every=64):
    logger = get_logger()
    logger.info(f"Formatted string.")
    return "\n".join(textwrap.wrap(string, every))


def write_to_txt_file(
    input_text, file_name, output_directory, mode="append", encoding="utf-8"
):
    """
    Specify any mode except for 'append' for write and replace.
    """
    output_file_path = os.path.join(output_directory, f"{file_name}.txt")
    with open(
        output_file_path, "a" if mode == "append" else "w", encoding=encoding
    ) as f:
        f.write(("\n" if mode == "append" and f.tell() > 0 else "") + input_text)


def load_text_from_file(txt_file_path):
    try:
        with open(txt_file_path, "r") as f:
            return f.read()
    except:
        return print(f"Failed to open .txt file at path: {txt_file_path}")


def open_txt_file(file_path):
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", file_path], check=True)
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", file_path], check=True)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
