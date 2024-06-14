"""
proxy.py
20230228
"""
from selenium.webdriver.common.proxy import Proxy, ProxyType
import urllib


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


def set_proxy_4_urllib_request(ip_port: str):
    """
    setup proxy
    :param ip_port: str or None, proxy server ip address with or without
        protocol prefix, eg: "127.0.0.1:7890", "http://127.0.0.1:7890".
    :return: proxies, dict with keys "http" and "https" or None.
    """
    if ip_port is None:
        proxies = None
    else:
        if not ip_port.startswith('http'):
            ip_port = 'http://' + ip_port
        proxies = {
            'http': ip_port,
            'https': ip_port
        }
        proxy_support = urllib.request.ProxyHandler(proxies)
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)
    return proxies


def get_proxy_4_requests(ip_port: str):
    """
    setup proxy
    :param ip_port: str or None, proxy server ip address with or without
        protocol prefix, eg: "127.0.0.1:7890", "http://127.0.0.1:7890".
    :return: proxies, dict with keys "http" and "https" or None.
    """
    if ip_port is None:
        proxies = None
    else:
        if not ip_port.startswith('http'):
            ip_port = 'http://' + ip_port
        proxies = {
            'http': ip_port,
            'https': ip_port
        }
    return proxies


if __name__ == "__main__":
    # get my ip
    import json
    set_proxy_4_urllib_request('127.0.0.1:7897')
    url = "http://ip-api.com/json"  # ipv4
    response = urllib.request.urlopen(url)
    data = json.load(response)
    if data['status'] == 'success':
        ip = data['query']
        print(f'ip: {ip}')
        print(f'details: {data}')
    else:
        print(f'failed, try agin: {data}')



