# VPN
import logging
from ..utility.logger import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

from ..utility.decorator import retry

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from nordvpn_switcher import initialize_VPN, rotate_VPN, terminate_VPN

from urllib.error import URLError
import socket
from typing import Tuple, Any


@retry(URLError, "simple")
def connect_to_vpn(country_list):
    vpn_settings = initialize_VPN(area_input=country_list)
    logger.info(f"Connecting to NordVPN with settings {vpn_settings}...")
    rotate_VPN(vpn_settings)
    return vpn_settings


def disconnect_from_vpn(vpn_settings):
    logger.info(f"Disconnecting from NordVPN with settings {vpn_settings}...")
    terminate_VPN(vpn_settings)


# INTERNET
# SELENIUM
def setup_browser(
    browser: str = "firefox", explicit_wait_seconds: int = 10
) -> Tuple[Any, Any]:
    options = Options()
    # choose browser
    if browser == "firefox":
        options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
        browser_object = webdriver.Firefox(options=options)

    wait_object = WebDriverWait(
        browser_object, explicit_wait_seconds
    )  # set up explicit waits

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


def check_internet(website):
    try:
        socket.create_connection((website, 80))
        return True
    except OSError:
        return False
