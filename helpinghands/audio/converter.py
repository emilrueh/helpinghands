from ..utility.logger import get_logger

logger = get_logger()

from pydub import AudioSegment


def ogg_to_mp3(input_file, output_file):
    AudioSegment.from_ogg(input_file).export(output_file, format="mp3")
    logger.info(f"Converted: {input_file} to {output_file}")
    return output_file


def combine_audio_files(input_files, output_file):
    segments = [AudioSegment.from_ogg(file) for file in input_files]
    combined = sum(segments, AudioSegment.empty())
    combined.export(output_file, format="ogg")
    logger.info(f"Combined files into: {output_file}")
    return output_file
