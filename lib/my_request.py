"""
my_request.py
20240412
"""

import urllib
import random
from urllib.error import URLError, HTTPError
from lib.proxy import set_proxy_4_urllib_request


def urlopen_with_retry(url, headers=dict(), retry_time=3, time_out=20,
                       raise_error_if_failed=True, proxy_ip_port=None):
    """
    load content from url with given headers. Retry if error occurs.
    Args:
        url (str): url.
        headers (dict): request headers. Default: {}.
        retry_time (int): max retry time. Default: 3.
        time_out (int): time out in seconds. Default: 10.
        raise_error_if_failed (bool): whether to raise error if failed.
            Default: True.
        proxy_ip_port(str|None): proxy server ip address with or without
            protocol prefix, eg: "127.0.0.1:7890", "http://127.0.0.1:7890".
            Default: None

    Returns:
        content(str|None): url content. None will be returned if failed.

    """
    set_proxy_4_urllib_request(proxy_ip_port)
    req = urllib.request.Request(url=url, headers=headers)
    for r in range(retry_time):
        try:
            content = urllib.request.urlopen(req, timeout=time_out).read()
            return content
        except HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
            s = random.randint(3, 7)
            print(f'random sleeping {s} seconds and doing {r + 1}/{retry_time}'
                  f'-th retrying...')
        except URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
            s = random.randint(3, 7)
            print(f'random sleeping {s} seconds and doing {r + 1}/{retry_time}'
                  f'-th retrying...')
    if raise_error_if_failed:
        raise ValueError(f'Failed to open {url} after trying {retry_time} '
                         f'times!')
    else:
        return None


