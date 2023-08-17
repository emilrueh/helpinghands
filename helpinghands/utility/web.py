import logging
from ..utility.logger import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

from ..utility.decorator import retry

# from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from selenium.common.exceptions import (
    WebDriverException,
    NoSuchWindowException,
    InvalidSessionIdException,
    SessionNotCreatedException,
)

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


@dataclass
class WebConfig:
    browser: str = "chrome"
    explicit_wait_seconds: int = 10
    headless: bool = True
    proxy_config: Optional[Dict[str, str]] = None
    remote_env: str = "DOCKER_ENV"
    original_ip: Optional[str] = None


# SELENIUM
# ---> GEN2
@retry((SessionNotCreatedException, ConnectionResetError), time_mode="simple")
def setup_browser(config: WebConfig) -> Tuple[Any, Any]:
    # loading config
    browser = config.browser
    explicit_wait_seconds = config.explicit_wait_seconds
    headless = config.headless
    proxy_config = config.proxy_config
    remote_env = config.remote_env

    # Check for the Docker environment
    in_docker = os.getenv(remote_env) is not None

    # Setup for Firefox
    if browser == "firefox":
        logger.warning(f"Firefox is deprecated. Please use Chrome instead.")
        options = webdriver.FirefoxOptions()

        # If running in headless mode
        if headless:
            options.add_argument("--headless")
        # start with or without a previously configured proxy
        if proxy_config:
            options.proxy = proxy_config
        # Path to Firefox binary in docker
        if in_docker:
            options.binary_location = "/usr/bin/firefox"
            service_log_path = "/app/data/geckodriver.log"
        else:
            options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
            service_log_path = None

        browser_object = webdriver.Firefox(
            options=options, service=FirefoxService(log_path=service_log_path)
        )
    # Setup for Chrome
    elif browser == "chrome":
        options = ChromeOptions()
        seleniumwire_options = None

        if headless:
            options.add_argument("--headless")
        if proxy_config:
            logger.debug(f"Setting proxy options: {proxy_config}")
            seleniumwire_options = setup_proxy_wire(proxy_config=proxy_config)

        # Path to Chrome binary in docker (this is only an example, adjust based on your docker setup)
        if in_docker:
            options.binary_location = "/usr/bin/google-chrome"
            service_log_path = "/app/data/chromedriver.log"
        else:
            # Default path to Chrome binary on most systems; adjust if yours is different
            options.binary_location = (
                r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            )
            service_log_path = None

        print(seleniumwire_options)
        browser_object = webdriver.Chrome(
            seleniumwire_options=seleniumwire_options,
            options=options,
            service=ChromeService(
                log_path=service_log_path, service_args=["--verbose"]
            ),
        )
        time.sleep(1)
    else:
        raise ValueError(
            f"{browser} browser is not available. Please use Firefox or Chrome."
        )

    if browser_object:
        wait_object = WebDriverWait(browser_object, explicit_wait_seconds)
        logger.info(f"Current IP: {get_current_ip(browser_object)}")
        return browser_object, wait_object


@retry(
    (
        NoSuchWindowException,
        InvalidSessionIdException,
        ConnectionError,
        WebDriverException,
    ),
    time_mode="advanced",
)
def get_website(website, selenium_browser, selenium_wait, config: WebConfig):
    browser = selenium_browser
    wait = selenium_wait
    try:
        logger.info(f"Accessing url: {website}")
        browser.get(website)  # <= open website
    except (NoSuchWindowException, InvalidSessionIdException, WebDriverException) as e:
        logger.warning(f"{type(e).__name__} encountered: {e}")
        has_internet = check_internet()
        if has_internet:
            browser, wait = rotate_ip(browser_object=browser, config=config)
            raise
        else:
            raise ConnectionError(f"No internet connection")
    return browser, wait


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
def get_original_ip():
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


@retry(RuntimeError, "medium")
def rotate_ip(browser_object, config: WebConfig):
    old_ip = get_current_ip(browser_object)

    if browser_object:
        browser_object.quit()
    browser_object, wait_object = setup_browser(config=config)
    new_ip = get_current_ip(browser_object=browser_object)

    if old_ip != new_ip != config.original_ip:
        print(f"Rotated IP: {old_ip} -> {new_ip}")
        return browser_object, wait_object
    else:
        raise RuntimeError("Failed to change IP. Trying again...")


# BEAUTIFUL SOUP
def make_soup(browser, new_soup=True, do_print=True):
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
    logger.info(f"Disconnecting from NordVPN with settings {vpn_settings}...")
    terminate_VPN(vpn_settings)


# OTHER
def check_internet(website: str = "https://www.duckduckgo.com"):
    try:
        socket.create_connection((website, 80))
        return True
    except OSError:
        return False
