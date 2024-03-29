"""
proxy.py
20230228
"""

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

from selenium.webdriver.common.proxy import Proxy, ProxyType


def get_proxy(ip_port: str):
    """
    setup proxy
    :param ip_port: str, proxy server ip address without protocol prefix,
        eg: "127.0.0.1:7890"
    :return: proxy (instance of selenium.webdriver.common.proxy.Proxy)
    Then the proxy could be to webdriver.Chrome:
        capabilities = webdriver.DesiredCapabilities.CHROME
        proxy.add_to_capabilities(capabilities)
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            desired_capabilities=capabilities)
    """
    proxy = Proxy()
    proxy.proxy_type = ProxyType.MANUAL
    proxy.http_proxy = ip_port
    proxy.ssl_proxy = ip_port
    return proxy

