from ..utility.logger import get_logger
from ..utility.decorator import retry
from ..utility.helper import log_exception

# from selenium import webdriver
from seleniumwire import webdriver
from seleniumwire.thirdparty.mitmproxy.exceptions import OptionsError

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.proxy import Proxy, ProxyType

from selenium.common.exceptions import SessionNotCreatedException

from bs4 import BeautifulSoup
from nordvpn_switcher import initialize_VPN, rotate_VPN, terminate_VPN

from urllib.error import URLError
import socket
from typing import Tuple, Any
import time
import os
import requests
import re

from dataclasses import dataclass
from typing import Optional, Dict, Any

import subprocess

BROWSER = None
WAIT = None


@dataclass
class WebConfig:
    browser: str = "chrome"
    explicit_wait_seconds: int = 10
    headless: bool = True
    proxy_config: Optional[Dict[str, str]] = None
    remote_env: str = "DOCKER_ENV"
    original_ip: Optional[str] = None
    autoplay_vids: bool = False


def check_versions_and_paths():
    chrome_version = subprocess.getoutput("google-chrome --version")
    chrome_path = subprocess.getoutput("which google-chrome")

    chromedriver_version = subprocess.getoutput("chromedriver --version")
    chromedriver_path = subprocess.getoutput("which chromedriver")

    return (chrome_version, chrome_path, chromedriver_version, chromedriver_path)


# SELENIUM
@retry((Exception), "advanced")
def open_website(
    url,
    browser_config: WebConfig = WebConfig,
    with_proxy: bool = True,
):
    logger = get_logger()

    global BROWSER
    global WAIT

    # BROWSER SETUP
    if not BROWSER:
        try:
            logger.debug(
                f"Setting up browser {'with' if with_proxy else 'without'} Proxy..."
            )
            BROWSER, WAIT = setup_browser(browser_config, with_proxy)
        except OptionsError as e:
            log_exception(e, log_level="Exception", verbose=True)
            return  # NO RETRY
        except Exception as e:
            log_exception(e)
            raise  # RETRY

    if BROWSER:
        # OPENING URL
        try:
            logger.debug(f"Opening URL: {url}")
            BROWSER.get(url)
        except KeyboardInterrupt:
            quit()
        except Exception as e:
            # CHECKING FOR CONNECTION
            if check_internet():
                has_internet = True
            else:
                has_internet = False

            # ROTATING IP
            if with_proxy and has_internet:
                logger.info("\n|----- R O T A T I N G   IP -----|\n")
                BROWSER.quit()
                BROWSER = None
                WAIT = None
                raise  # RETRY

            # else logging exception as true error
            log_exception(e, log_level="Exception", verbose=True)

    return BROWSER, WAIT


# -> GEN4
@retry(
    (SessionNotCreatedException),
    "simple",
)
def setup_browser(config: WebConfig, with_proxy: bool = True) -> Tuple[Any, Any]:
    logger = get_logger()
    # logger.debug(check_versions_and_paths())

    # loading config
    browser = config.browser
    explicit_wait_seconds = config.explicit_wait_seconds
    headless = config.headless
    proxy_config = config.proxy_config
    remote_env = config.remote_env
    autoplay_videos = config.autoplay_vids

    # Check for the Docker environment
    in_docker = os.getenv(remote_env) is not None

    # Setup for Chrome
    if browser == "chrome":
        options = ChromeOptions()
        seleniumwire_options = None

        if not autoplay_videos:
            options.add_argument("--autoplay-policy=document-user-activation-required")

        if headless or in_docker:
            logger.debug("Running headless...")
            options.add_argument("--disable-gpu")
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")  # Bypass OS-level sandbox
            options.add_argument(
                "--disable-dev-shm-usage"
            )  # Overcome limited resource issues in Docker
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-webgl")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--log-level=3")  # Only show fatal errors
            options.add_experimental_option(
                "prefs",
                {
                    "profile.default_content_setting_values.notifications": 2,
                    "profile.managed_default_content_settings.images": 2,
                    "profile.managed_default_content_settings.javascript": 1,
                    "profile.managed_default_content_settings.plugins": 1,
                    "profile.managed_default_content_settings.popups": 2,
                    "profile.managed_default_content_settings.geolocation": 2,
                    "profile.managed_default_content_settings.media_stream": 2,
                    "profile.default_content_settings.cookies": 2,
                    "profile.block_third_party_cookies": True,
                },
            )

        if with_proxy and proxy_config:
            logger.debug(f"Setting proxy options:\n{proxy_config}")
            seleniumwire_options = setup_proxy_wire(proxy_config=proxy_config)

        if in_docker:
            binary_location = "/usr/bin/chromedriver"
            service_log_path = "/app/data/chromedriver.log"
        else:
            binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            service_log_path = None

        logger.debug(f"seleniumwire_options = {seleniumwire_options}")
        browser_object = webdriver.Chrome(
            seleniumwire_options=seleniumwire_options,
            options=options,
            service=ChromeService(
                log_path=service_log_path,
                service_args=["--verbose"],
                # executable_path=binary_location,
            ),
        )
        time.sleep(3)
        browser_object.set_page_load_timeout(60)  # SET PAGE LOAD LIMIT
    else:
        raise ValueError(
            f"{browser} browser is not available. Please use Chrome (Firefox is deprecated)."
        )

    if browser_object:
        wait_object = WebDriverWait(browser_object, explicit_wait_seconds)
        show_ip = False  # needs to be part of config
        if with_proxy and show_ip:
            logger.info(f"Current IP: {get_current_ip(browser_object)}")
        return browser_object, wait_object


# chrome
def setup_proxy_wire(
    proxy_config: dict = {"host": None, "username": None, "password": None},
    for_selenium: bool = True,
) -> Proxy:
    host = proxy_config["host"]
    username = proxy_config["username"]
    password = proxy_config["password"]

    if not all([host, username, password]):
        raise ValueError("All proxy details must be provided.")

    proxy = {
        "http": f"http://{username}:{password}@{host}",
        "https": f"http://{username}:{password}@{host}",
    }

    if for_selenium:
        return {"proxy": proxy}
    return proxy


# PROXY
# firefox (deprecated)
def setup_proxy_simple(host: str, username: str, password: str) -> Proxy:
    if not all([host, username, password]):
        raise ValueError("All BrightData proxy details must be provided.")

    # Removing the "http://" scheme
    proxy_url = host

    proxy_config = {
        "httpProxy": proxy_url,
        "sslProxy": proxy_url,
        "proxyType": ProxyType.MANUAL,
    }

    proxy = Proxy(proxy_config)

    return proxy


# manual test
def test_proxy(proxy_host, proxy_user, proxy_pass):
    proxies = {
        "http": f"http://{proxy_user}:{proxy_pass}@{proxy_host}",
        "https": f"https://{proxy_user}:{proxy_pass}@{proxy_host}",
    }
    url = "https://lumtest.com/myip.json"
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code

        data = response.json()
        print(f"Response from the server: {data}")
        return True
    except requests.RequestException as e:
        print(f"Failed to connect using the proxy. Error: {e}")
        return False


# IPs
def listen_on_port(address="0.0.0.0", port=8080):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((address, port))
    s.listen(1)
    conn, addr = s.accept()
    return s


def get_original_ip():
    logger = get_logger()
    try:
        response = requests.get("https://api.ipify.org?format=json")
        ip = response.json()["ip"]
        return ip
    except Exception as e:
        logger.error(f"Failed to get original IP. Error: {e}")
        return None


@retry(ValueError, "simple")
def get_current_ip(
    browser_object,
    IP_SERVICES: list = [
        "https://api.ipify.org?format=json",
        "https://icanhazip.com",
        "http://checkip.amazonaws.com",
        "http://ipinfo.io/ip",
        "https://httpbin.org/ip",
    ],
):
    for service in IP_SERVICES:
        browser_object.get(service)
        raw_content = browser_object.page_source.strip()

        # If using ipify, we'll expect a JSON response
        if service == "https://api.ipify.org?format=json":
            match = re.search(r'{"ip":"(.*?)"', raw_content)
        else:
            # For other services, just extract the IP from the page content
            match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", raw_content)

        if match:
            ip_address = match.group(1)
            return ip_address

    # If the function hasn't returned by this point, raise an error to @retry
    raise ValueError(f"Failed to fetch IP from either service")


# @retry(RuntimeError, "medium")
# def rotate_ip(browser_object, config: WebConfig):
#     try:
#         old_ip = get_current_ip(browser_object)
#     except Exception as e:
#         old_ip = "000.000.000"
#         logger.warning(f"Failed to fetch old_ip: {type(e).__name__}: {e}")

#     if browser_object:
#         browser_object.quit()
#     browser_object, wait_object = setup_browser(config=config)
#     new_ip = get_current_ip(browser_object=browser_object)

#     if old_ip != new_ip != config.original_ip:
#         print(f"Rotated IP: {old_ip} -> {new_ip}")
#         return browser_object, wait_object
#     else:
#         raise RuntimeError("Failed to change IP. Trying again...")


@retry(RuntimeError, "medium")
def rotate_ip(browser_object, config: WebConfig):
    old_ip = get_current_ip(browser_object) if browser_object else "000.000.000"

    if browser_object:
        browser_object.quit()
    browser_object, wait_object = setup_browser(config=config)
    new_ip = get_current_ip(browser_object)

    if old_ip != new_ip and new_ip != config.original_ip:
        print(f"Rotated IP: {old_ip} -> {new_ip}")
        return browser_object, wait_object
    else:
        raise RuntimeError("Failed to change IP. Trying again...")


# BEAUTIFUL SOUP
def make_soup(browser, new_soup=True, do_print=True):
    logger = get_logger()
    fresh_soup = "Making Soup..."
    old_soup = "Refreshing Soup..."

    if new_soup:
        if logger:
            logger.debug(fresh_soup)
        elif do_print:
            print(fresh_soup)
    else:
        if logger:
            logger.debug(old_soup)
        elif do_print:
            print(old_soup)

    return BeautifulSoup(browser.page_source, "html.parser")


# VPN
# @retry(URLError, "simple")
# def connect_to_vpn(country_list):
#     vpn_settings = initialize_VPN(area_input=country_list)
#     logger.info(f"Connecting to NordVPN with settings {vpn_settings}...")
#     rotate_VPN(vpn_settings)
#     return vpn_settings


@retry(URLError, "simple")
def connect_to_vpn(country_list, use_env_credentials=False):
    logger = get_logger()

    logger.info(f"use_env_credentials = {use_env_credentials}")
    use_settings_file = None
    if use_env_credentials:
        logger.info(f"For NordVPN the OS name is: {os.name}")
        # if os.name == "posix":  # Ensure it's a Linux environment
        # Get credentials from environment variables
        username = os.getenv("NORDVPN_USERNAME")
        password = os.getenv("NORDVPN_PASSWORD")

        if not username or not password:
            logger.error("NordVPN credentials not found in environment variables.")
            return None

        current_directory = os.getcwd()
        logger.info(f"Current working directory: {current_directory}")

        nordvpn_settings_path = "/app/nordvpn_settings.txt"
        # Save the credentials to nordvpn_settings.txt
        credentials = {"opsys": "Linux", "credentials": [[username], [password]]}
        with open(nordvpn_settings_path, "w") as f:
            f.write(str(credentials))

        logger.info(f"Written credentials to nordvpn_settings.txt: {credentials}")

        with open(nordvpn_settings_path, "r") as f:
            file_content = f.read()
        logger.info(f"Contents of nordvpn_settings.txt: {file_content}")

        if os.path.exists("nordvpn_settings.txt"):
            logger.info("nordvpn_settings.txt exists.")
        else:
            logger.warning("nordvpn_settings.txt does not exist.")

        use_settings_file = 1

    vpn_settings = initialize_VPN(
        stored_settings=use_settings_file, area_input=country_list
    )
    logger.info(f"Connecting to NordVPN with settings {vpn_settings}...")
    rotate_VPN(vpn_settings)
    return vpn_settings


def disconnect_from_vpn(vpn_settings):
    logger = get_logger()
    logger.info(f"Disconnecting from NordVPN with settings {vpn_settings}...")
    terminate_VPN(vpn_settings)


# OTHER
# def check_internet(website: str = "https://www.duckduckgo.com"):
#     try:
#         socket.create_connection((website, 80))
#         return True
#     except OSError:
#         return False


def check_internet(website: str = "https://www.duckduckgo.com"):
    try:
        response = requests.get(website)
        return True if response.status_code == 200 else False
    except requests.RequestException:
        return False
