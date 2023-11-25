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
