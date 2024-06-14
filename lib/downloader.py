"""
downloader.py
20210624
"""
import time
from lib import IDM
import requests
import os
import random
from tqdm import tqdm
from threading import Thread
from lib.proxy import get_proxy_4_requests


def _download(urls, save_path, time_sleep_in_seconds=5, is_random_step=True,
              verbose=False, proxy_ip_port=None):
    """
    download file from given urls and save it to given path
    :param urls: str, urls
    :param save_path: str, full path
    :param time_sleep_in_seconds: int, sleep seconds after call
    :param is_random_step: bool, whether random sample the time step between two
        adjacent download requests. If True, the time step will be sampled
        from Uniform(0.5t, 1.5t), where t is the given time_step_in_seconds.
        Default: True.
    :param verbose: bool, whether to display time step information.
        Default: False
    :param proxy_ip_port: str or None, proxy server ip address with or without
        protocol prefix, eg: "127.0.0.1:7890", "http://127.0.0.1:7890".
    :return: None
    """

    def __download(urls, save_path, proxy_ip_port):
        head, tail = os.path.split(save_path)
        # debug
        # print(f'downloading {tail}')
        proxies = get_proxy_4_requests(proxy_ip_port)
        r = requests.get(urls, stream=True, proxies=proxies)
        # file size in MB
        length = round(int(r.headers['content-length']) / 1024**2, 2)
        process_bar = tqdm(
            colour='blue', total=length, unit='MB',desc=tail, initial=0)

        if '' != head:
            os.makedirs(head, exist_ok=True)

        for part in r.iter_content(1024 ** 2):
            process_bar.update(1)
            with open(save_path, 'ab') as file:
                file.write(part)
        r.close()

    # set daemon as False to continue downloading even if the main threading
    # has been killed due to KeyboardInterrupt
    t = Thread(
        target=__download, args=(urls, save_path, proxy_ip_port), daemon=False)
    t.start()

    if is_random_step:
        time_sleep_in_seconds = random.uniform(
            0.5 * time_sleep_in_seconds,
            1.5 * time_sleep_in_seconds,
        )
    if verbose:
        print(f'\t random sleep {time_sleep_in_seconds: .2f} seconds')
    time.sleep(time_sleep_in_seconds)


class Downloader(object):
    def __init__(self, downloader=None, is_random_step=True,
                 proxy_ip_port=None):
        """
        :param downloader: None or str, the downloader's name.
            if downloader is None, 'request' will be used to
            download files; if downloader is 'IDM', the
            "Internet Downloader Manager" will be used to download
            files; or a ValueError will be raised.
        :param is_random_step: bool, whether random sample the time step between
            two adjacent download requests. If True, the time step will be
            sampled from Uniform(0.5t, 1.5t), where t is the given
            time_step_in_seconds. Default: True.
        :param proxy_ip_port: str or None, proxy server ip address with or without
            protocol prefix, eg: "127.0.0.1:7890", "http://127.0.0.1:7890".
            (only useful for None|"request" downloader)
            Default: None
        """
        super(Downloader, self).__init__()
        if downloader is not None and downloader.lower() not in ['idm']:
            raise ValueError(
                f'''ERROR: Unsupported downloader: {downloader}, '''
                f'''we currently only support'''
                f''' None (means python's requests) or "IDM" '''
            )

        self.downloader = downloader
        self.is_random_step = is_random_step
        self.proxy_ip_port = proxy_ip_port

    def download(self, urls, save_path, time_sleep_in_seconds=5):
        """
        download file from given urls and save it to given path
        :param urls: str, urls
        :param save_path: str, full path
        :param time_sleep_in_seconds: int, sleep seconds after call
        :return: None
        """
        if self.downloader is None:
            _download(
                urls=urls,
                save_path=save_path,
                time_sleep_in_seconds=time_sleep_in_seconds,
                is_random_step=self.is_random_step,
                proxy_ip_port=self.proxy_ip_port
            )
        elif self.downloader.lower() == 'idm':
            IDM.download(
                urls=urls,
                save_path=save_path,
                time_sleep_in_seconds=time_sleep_in_seconds,
                is_random_step=self.is_random_step
            )
