from ..utility.logger import get_logger

import functools, time


def retry(exceptions, time_mode: str = "medium"):
    logger = get_logger()
    """
    A retry decorator that applies a backoff strategy for retries and controls the
    number of retry attempts based on the selected time_mode. It will retry the decorated
    function upon raising specified exceptions.

    The decorator supports four modes represented by a string determining: total tries, initial wait, backoff factor.

        'simple': 2 total tries, 1 second initial wait, backoff factor of 2.
        'medium': 3 total tries, 2 seconds initial wait, backoff factor of 3.
        'advanced': 4 total tries, 4 seconds initial wait, backoff factor of 4.
        'verbose': 6 total tries, 6 seconds initial wait, backoff factor of 3.

        (If no time_mode or an unrecognized time_mode is specified, it defaults to 'medium'.)

    Returns:
        A decorator which can be used to decorate a function with the retry logic.

    Raises:
        The exceptions specified in the 'exceptions' parameter if all retry attempts fail.
    """

    if time_mode == "simple":
        total_tries = 2
        initial_wait = 1
        backoff_factor = 2
    elif time_mode == "medium":
        total_tries = 3
        initial_wait = 2
        backoff_factor = 3
    elif time_mode == "advanced":
        total_tries = 4
        initial_wait = 4
        backoff_factor = 4
    elif time_mode == "verbose":
        total_tries = 6
        initial_wait = 6
        backoff_factor = 3
    else:
        total_tries = 3
        initial_wait = 2
        backoff_factor = 3

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait_time = initial_wait
            for attempt in range(total_tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt >= total_tries - 1:
                        logger.warning(f"All retries failed after {attempt} attempts.")
                        raise
                    else:
                        logger.warning(
                            f"{str(e).split('  ')[0]}: Retrying attempt {attempt+1} in {round(wait_time, 2)} seconds..."
                        )
                        time.sleep(wait_time)
                        wait_time *= backoff_factor

        return wrapper

    return decorator


def time_execution(logger, ndigits=3, time_mode="seconds", log_mode="info"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"Executing {func.__name__}...")
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()

            if log_mode == "info":
                if time_mode == "seconds":
                    logger.info(f"{func.__name__} completed in {round(end_time - start_time, ndigits)} seconds.")
                elif time_mode == "minutes":
                    logger.info(
                        f"{func.__name__} completed in {round(((end_time - start_time) / 60), ndigits)} minutes."
                    )
                elif time_mode == "hours":
                    logger.info(
                        f"{func.__name__} completed in {round((((end_time - start_time) / 60) /60), ndigits)} hours."
                    )
                else:
                    logger.info(
                        f"{func.__name__} completed in {round(end_time - start_time, ndigits)}s {round(end_time - start_time, ndigits)/60} min {(round(end_time - start_time, ndigits)/60)/60} h."
                    )
            else:
                logger.warning("No other log_mode than 'info' implemented at this stage. Please select default.")

            return result

        return wrapper

    return decorator
