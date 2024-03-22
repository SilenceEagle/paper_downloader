"""
downloader.py
20210624
"""
import time
from lib import IDM
import requests
import os
import random


def _download(urls, save_path, time_sleep_in_seconds=5, is_random_step=True,
              verbose=False):
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
    :return: None
    """
    r = requests.get(urls, stream=True)
    head, tail = os.path.split(save_path)
    if '' != head:
        os.makedirs(head, exist_ok=True)

    with open(save_path, 'wb') as f:
        for chunck in r.iter_content(1024):
            f.write(chunck)
    r.close()
    if is_random_step:
        time_sleep_in_seconds = random.uniform(
            0.5 * time_sleep_in_seconds,
            1.5 * time_sleep_in_seconds,
        )
    if verbose:
        print(f'\t random sleep {time_sleep_in_seconds: .2f} seconds')
    time.sleep(time_sleep_in_seconds)


class Downloader(object):
    def __init__(self, downloader=None):
        """
        :param downloader: None or str, the downloader's name.
            if downloader is None, 'request' will be used to
            download files; if downloader is 'IDM', the
            "Internet Downloader Manager" will be used to download
            files; or a ValueError will be raised.
        """
        super(Downloader, self).__init__()
        if downloader is not None and downloader.lower() not in ['idm']:
            raise ValueError(
                f'''ERROR: Unsupported downloader: {downloader}, '''
                f'''we currently only support'''
                f''' None (means python's requests) or "IDM" '''
            )
        self.downloader = downloader

    def download(self, urls, save_path, time_sleep_in_seconds=5,
                 is_random_step=True):
        """
        download file from given urls and save it to given path
        :param urls: str, urls
        :param save_path: str, full path
        :param time_sleep_in_seconds: int, sleep seconds after call
        :param is_random_step: bool, whether random sample the time step between
            two adjacent download requests. If True, the time step will be
            sampled from Uniform(0.5t, 1.5t), where t is the given
            time_step_in_seconds. Default: True.
        :return: None
        """
        if self.downloader is None:
            _download(
                urls=urls,
                save_path=save_path,
                time_sleep_in_seconds=time_sleep_in_seconds,
                is_random_step=is_random_step
            )
        elif self.downloader.lower() == 'idm':
            IDM.download(
                urls=urls,
                save_path=save_path,
                time_sleep_in_seconds=time_sleep_in_seconds,
                is_random_step=is_random_step
            )
