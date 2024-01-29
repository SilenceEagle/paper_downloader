"""
downloader.py
20210624
"""
import time
from lib import IDM
import requests
import os


def _download(urls, save_path, time_sleep_in_seconds=5):
    """
    download file from given urls and save it to given path
    :param urls: str, urls
    :param save_path: str, full path
    :param time_sleep_in_seconds: int, sleep seconds after call
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
                time_sleep_in_seconds=time_sleep_in_seconds
            )
        elif self.downloader.lower() == 'idm':
            IDM.download(
                urls=urls,
                save_path=save_path,
                time_sleep_in_seconds=time_sleep_in_seconds
            )
