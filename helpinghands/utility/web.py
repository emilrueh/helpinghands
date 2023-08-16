# VPN
import logging
from ..utility.logger import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

from ..utility.decorator import retry

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.proxy import Proxy, ProxyType

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import (
    WebDriverException,
    NoSuchWindowException,
    InvalidSessionIdException,
)

from bs4 import BeautifulSoup
from nordvpn_switcher import initialize_VPN, rotate_VPN, terminate_VPN

from urllib.error import URLError
import socket
from typing import Tuple, Any
import time
import os


# SELENIUM
# ---> GEN2
def setup_browser(
    browser: str = "firefox",
    explicit_wait_seconds: int = 10,
    headless: bool = True,
    proxy: Proxy = None,
    remote_env: str = "DOCKER_ENV",
) -> Tuple[Any, Any]:
    # Check for the Docker environment
    in_docker = os.getenv(remote_env) is not None

    # Setup for Firefox
    if browser == "firefox":
        options = webdriver.FirefoxOptions()

        # If running in headless mode
        if headless:
            options.add_argument("--headless")
        # start with or withtout a previously configured proxy
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

    else:
        raise ValueError(f"{browser} browser is not available. Please use Firefox.")

    if browser_object:
        wait_object = WebDriverWait(browser_object, explicit_wait_seconds)

        return browser_object, wait_object


@retry(
    (
        NoSuchWindowException,
        InvalidSessionIdException,
        ConnectionError,
        WebDriverException,
    )
)
def get_website(website, selenium_browser, selenium_wait, VPN_REGIONS, proxy):
    browser = selenium_browser
    wait = selenium_wait
    try:
        browser.get(website)  # <= open website
    except (NoSuchWindowException, InvalidSessionIdException) as d:
        logger.warning(d)
        if browser:
            browser.quit()
        browser, wait = setup_browser()  # reinitialize browser
        raise
    except WebDriverException as e:
        logger.warning(e)
        has_internet = check_internet("www.google.com")  # check internet
        if has_internet:
            if VPN_REGIONS:
                logger.warning(f"{e} connecting to NordVPN...")
                connect_to_vpn(VPN_REGIONS)  # connecting to NordVPN
            if proxy:
                rotate_ip(browser, proxy)
            raise
        else:
            raise ConnectionError  # no internet
    return browser, wait


# PROXY
def setup_proxy_brightdata(
    host: str,
    username: str,
    password: str,
) -> Proxy:
    if not all([host, username, password]):
        raise ValueError("All BrightData proxy details must be provided.")

    proxy_config = {
        "httpProxy": host,
        "sslProxy": host,
        "ftpProxy": host,
        "socksUsername": username,
        "socksPassword": password,
        "proxyType": ProxyType.MANUAL,
    }

    return Proxy(proxy_config)


# IPs
def get_current_ip(browser_object):
    try:
        browser_object.get("https://httpbin.org/ip")
        element = WebDriverWait(browser_object, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "pre"))
        )
        ip_address = element.text.split('"origin": "')[1].split('"')[0]
        return ip_address
    except Exception as e:
        logger.error(f"Failed to fetch IP: {e}")
        return None


def rotate_ip(browser_object, proxy):
    old_ip = get_current_ip(browser_object)
    browser_object.quit()

    browser_object = setup_browser(browser="firefox", proxy=proxy)
    new_ip = get_current_ip(browser_object)

    logger.info(f"Rotated IP from {old_ip} to {new_ip}")
    return browser_object


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
def check_internet(website):
    try:
        socket.create_connection((website, 80))
        return True
    except OSError:
        return False
