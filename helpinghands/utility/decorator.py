import logging
from ..utility.logger import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

import functools, time


def retry(exceptions, mode: str = "simple"):
    """
    A retry decorator that applies a backoff strategy for retries and controls the
    number of retry attempts based on the selected mode. It will retry the decorated
    function upon raising specified exceptions.

    The decorator supports four modes represented by a string determining: total tries, initial wait, backoff factor.

        'simple': 2 total tries, 1 second initial wait, backoff factor of 2.
        'medium': 3 total tries, 2 seconds initial wait, backoff factor of 3.
        'advanced': 4 total tries, 4 seconds initial wait, backoff factor of 4.
        'verbose': 6 total tries, 6 seconds initial wait, backoff factor of 3.

        (If no mode or an unrecognized mode is specified, it defaults to 'simple'.)

    Returns:
        A decorator which can be used to decorate a function with the retry logic.

    Raises:
        The exceptions specified in the 'exceptions' parameter if all retry attempts fail.
    """

    if mode == "simple":
        total_tries = 2
        initial_wait = 1
        backoff_factor = 2
    elif mode == "medium":
        total_tries = 3
        initial_wait = 2
        backoff_factor = 3
    elif mode == "advanced":
        total_tries = 4
        initial_wait = 4
        backoff_factor = 4
    elif mode == "verbose":
        total_tries = 6
        initial_wait = 6
        backoff_factor = 3
    else:
        total_tries = 2
        initial_wait = 1
        backoff_factor = 2

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait_time = initial_wait
            for attempt in range(total_tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.info(f"Attempt {attempt}")
                    if attempt >= total_tries - 1:
                        logger.warning(f"All retries failed after {attempt} attempts.")
                        raise
                    else:
                        print(f"{str(e)}: Retrying in {round(wait_time, 2)} seconds...")
                        time.sleep(wait_time)
                        wait_time *= backoff_factor

        return wrapper

    return decorator


def time_execution(logger, ndigits=3, mode="s"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"Executing {func.__name__}...")
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            if mode == "s":
                logger.info(
                    f"{func.__name__} completed in {round(end_time - start_time, ndigits)} seconds."
                )
            elif mode == "m":
                logger.info(
                    f"{func.__name__} completed in {round(end_time - start_time, ndigits)/60} minutes."
                )
            elif mode == "h":
                logger.info(
                    f"{func.__name__} completed in {(round(end_time - start_time, ndigits)/60)/60} hours."
                )
            return result

        return wrapper

    return decorator
