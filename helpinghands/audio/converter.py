from ..utility.logger import get_logger

from pydub import AudioSegment


def convert_audio(input_file, output_file):
    logger = get_logger()
    input_type = input_file.split(".")[-1]
    output_type = output_file.split(".")[-1]

    if input_type not in ["wav", "ogg", "mp3"]:
        logger.error(f"Unsupported input file type: {input_type}")
        return None

    audio = AudioSegment.from_file(input_file, format=input_type)
    audio.export(output_file, format=output_type)
    logger.info(f"Converted: {input_file} to {output_file}")
    return output_file


def combine_audio_files(input_files, output_file):
    logger = get_logger()
    segments = [AudioSegment.from_ogg(file) for file in input_files]
    combined = sum(segments, AudioSegment.empty())
    combined.export(output_file, format="ogg")
    logger.info(f"Combined files into: {output_file}")
    return output_file
