from .data import (
    get_data_dir,
    backup_data,
    backup_df,
    json_save,
    json_read,
    flatten_data,
    json_to_df,
    save_dict_to_csv,
    create_df,
    swap_columns,
    load_from_csv,
    delete_duplicates,
    delete_duplicates_add_keywords,
    map_keywords_to_categories,
    find_and_assign_tags,
    add_relevant_tags,
    replace_values,
    contains_gmaps,
    manipulate_csv_data,
    insert_newlines,
    write_to_txt_file,
    load_text_from_file,
    open_txt_file,
)
from .settings import load_settings
from .logger import config_logger, LOGGER_NAME
from .tokenbucket import TokenBucket

from .decorator import retry, time_execution
from .helper import (
    log_exception,
    get_git_tree,
    colorize,
    get_variable_name,
    ensure_windows_os,
)

try:
    from .web import (
        WebConfig,
        setup_browser,
        get_website,
        setup_proxy_simple,
        setup_proxy_wire,
        test_proxy,
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

    warnings.warn(
        "The web.py module is disabled in the current env due to missing dependencies. All other helpinghands modules should work as expected."
    )
