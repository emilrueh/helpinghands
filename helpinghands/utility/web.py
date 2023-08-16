# VPN
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


# SELENIUM
# ---> GEN2
@retry((SessionNotCreatedException, ConnectionResetError), time_mode="simple")
def setup_browser(
    browser_config: dict = {
        "browser": "chrome",
        "explicit_wait_seconds": 10,
        "headless": True,
        "proxy": None,
        "remote_env": "DOCKER_ENV",
    }
) -> Tuple[Any, Any]:
    # loading config
    browser = browser_config["browser"]
    explicit_wait_seconds = browser_config["explicit_wait_seconds"]
    headless = browser_config["headless"]
    proxy = browser_config["proxy"]
    remote_env = browser_config["remote_env"]

    # Check for the Docker environment
    in_docker = os.getenv(remote_env) is not None

    # Setup for Firefox
    if browser == "firefox":
        options = webdriver.FirefoxOptions()

        # If running in headless mode
        if headless:
            options.add_argument("--headless")
        # start with or without a previously configured proxy
        if proxy:
            options.proxy = proxy
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
        if proxy:
            print(f"Setting proxy options: {proxy}")
            seleniumwire_options = proxy
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

        browser_object = webdriver.Chrome(
            seleniumwire_options=seleniumwire_options,
            options=options,
            service=ChromeService(log_path=service_log_path),
        )
        time.sleep(1)
    else:
        raise ValueError(f"{browser} browser is not available. Please use Firefox.")

    if browser_object:
        wait_object = WebDriverWait(browser_object, explicit_wait_seconds)
        print(f"Current IP: {get_current_ip(browser_object)}")
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
def get_website(
    website, selenium_browser, selenium_wait, browser_config, proxy_config, original_ip
):
    browser = selenium_browser
    wait = selenium_wait
    try:
        browser.get(website)  # <= open website
    except (NoSuchWindowException, InvalidSessionIdException, WebDriverException) as e:
        logger.warning(f"{type(e).__name__} encountered: {e}")
        has_internet = check_internet()
        if has_internet:
            browser, wait = rotate_ip(
                browser, browser_config, proxy_config, original_ip
            )
            raise
        else:
            raise ConnectionError(f"No internet connection")
    return browser, wait


# PROXY
# firefox
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
    proxy_config: dict = {"host": None, "username": None, "password": None}
) -> Proxy:
    host = proxy_config["host"]
    username = proxy_config["username"]
    password = proxy_config["password"]

    if not all([host, username, password]):
        raise ValueError("All proxy details must be provided.")

    proxy = {
        "proxy": {
            "http": f"http://{username}:{password}@{host}",
            "https": f"http://{username}:{password}@{host}",
        }
    }

    return proxy


# IPs
def get_original_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json")
        ip = response.json()["ip"]
        return ip
    except Exception as e:
        logger.error(f"Failed to get original IP. Error: {e}")
        return None


def get_current_ip(browser_object):
    try:
        browser_object.get("https://httpbin.org/ip")

        # Obtain the raw page source
        raw_content = browser_object.page_source

        # Look for the IP address in the raw content using a regular expression
        match = re.search(r'"origin": "(.*?)"', raw_content)
        if match:
            ip_address = match.group(1)
            return ip_address
        else:
            raise ValueError("Failed to extract IP address from page source")
    except Exception as e:
        logger.error(f"Failed to fetch IP: {e}")
        return None


def rotate_ip(browser_object, browser_config, proxy_config, original_ip):
    old_ip = get_current_ip(browser_object)

    attempts = 0
    while attempts < 3:
        attempts += 1

        if browser_object:
            browser_object.quit()
        proxy = setup_proxy_wire(proxy_config=proxy_config)
        browser_config["proxy"] = proxy
        browser_object, wait_object = setup_browser(browser_config=browser_config)
        new_ip = get_current_ip(browser_object)

        if old_ip != new_ip != original_ip:
            break
        else:
            print(
                f"IPs didn't change or reverted to original IP. Trying again with attempt {attempts}..."
            )
    if attempts == 3 and (old_ip == new_ip or new_ip == original_ip):
        raise Exception("Failed to change IP after 3 attempts.")
    else:
        print(
            f"Rotated IP from {old_ip} to {new_ip} {f'after {attempts} attempts' if attempts > 1 else ''}"
        )
        return browser_object, wait_object


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
