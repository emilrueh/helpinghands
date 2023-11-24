from .data import (
    get_data_dir,
    add_random_files,
    choose_random_file,
    clean_directory,
    remove_duplicate_words,
    extract_number,
    json_save,
    json_read,
    json_to_df,
    create_df,
    df_from_csv,
)
from .text import (
    insert_newlines,
    write_to_txt_file,
    load_text_from_file,
    open_txt_file,
)
from .settings import load_settings
from .logger import config_logger, LOGGER_NAME
from .tokenbucket import TokenBucket, api_rate_limit_wait

from .decorator import retry, time_execution
from .helper import (
    log_exception,
    get_git_tree,
    colorize,
    get_variable_name,
    ensure_windows_os,
    log_memory_usage,
)
from .image import (
    convert_byte_sizes,
    get_image_res,
    get_image,
    image_to_bytes,
    bytes_to_base64,
    image_to_base64str,
    get_file_size,
    compress_image,
)

try:
    from .web import (
        WebConfig,
        open_website,
        setup_browser,
        setup_proxy_wire,
        setup_proxy_simple,
        test_proxy,
        listen_on_port,
        get_original_ip,
        get_current_ip,
        rotate_ip,
        make_soup,
        connect_to_vpn,
        disconnect_from_vpn,
        check_internet,
    )
except ModuleNotFoundError:
    import warnings

    warnings.warn("'web' is disabled")
