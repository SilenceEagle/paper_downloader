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
from lib import graceful_exit

# a downloaded file smaller than this is almost certainly an error page
# (e.g. the OpenReview rate-limit json) rather than a real paper, so it will
# be re-downloaded instead of being treated as a valid file
MIN_VALID_FILE_SIZE = 10 * 1024  # 10 KB


def is_valid_downloaded_file(file_path):
    """
    whether file_path exists and is large enough to be a real downloaded
    file (tiny files are usually error pages from a failed download)
    :param file_path: str, full file path
    :return: bool
    """
    return os.path.exists(file_path) and \
        os.path.getsize(file_path) >= MIN_VALID_FILE_SIZE


def shorten_title(name, head_words=2, tail_words=1):
    """
    shorten a slugified paper title (words joined by '-') to "first
    head_words words...last tail_words words", e.g.
    "prompt-optimization...reasoning", so the downloaded log stays compact.
    :param name: str, the slugified paper title
    :param head_words: int, how many words to keep at the beginning of the
        title. Default: 2.
    :param tail_words: int, how many words to keep at the end of the title.
        Default: 1.
    :return: str, the shortened title
    """
    words = name.split('-')
    if len(words) <= head_words + tail_words:
        return name
    return '-'.join(words[:head_words]) + '...' + '-'.join(words[-tail_words:])


def _download(urls, save_path, time_sleep_in_seconds=5, is_random_step=True,
              verbose=False, proxy_ip_port=None, cookies=None):
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
    :param cookies: dict or None, cookies to send with the request, e.g. the
        cookies of the logged-in browser session. Default: None.
    :return: None
    """

    # do not start new downloads after the first Ctrl+C
    if graceful_exit.is_stop_requested():
        return

    def __download(urls, save_path, proxy_ip_port, cookies):
        head, tail = os.path.split(save_path)
        # debug
        # print(f'downloading {tail}')
        proxies = get_proxy_4_requests(proxy_ip_port)
        headers = {'User-Agent':
                   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/149.0.0.0 Safari/537.36'}
        max_retry_time = 5
        r = None
        for retry in range(max_retry_time):
            r = requests.get(urls, stream=True, proxies=proxies,
                             cookies=cookies, headers=headers)
            if r.status_code == 200:
                break
            if r.status_code == 429:
                # OpenReview rate limits the API to 5 requests per ~17
                # seconds, wait a while and retry
                print(f'[429 rate limited] retrying {shorten_title(tail)} '
                      f'in 30 seconds ({retry + 1}/{max_retry_time})...')
                r.close()
                time.sleep(30)
                continue
            print(f'failed to download {shorten_title(tail)}: '
                  f'HTTP {r.status_code}')
            r.close()
            return
        if r.status_code != 200:
            print(f'failed to download {shorten_title(tail)}: still rate '
                  f'limited after {max_retry_time} retries')
            return
        content_type = r.headers.get('content-type', '')
        if 'json' in content_type.lower() or 'html' in content_type.lower():
            # error pages (e.g. the rate-limit json) are never valid files
            print(f'failed to download {shorten_title(tail)}: got an error '
                  f'page (content-type: {content_type})')
            r.close()
            return
        content_length = r.headers.get('content-length')
        if content_length is None:
            print(f'\twarning: no content-length header for '
                  f'{shorten_title(tail)}')
            length = None  # tqdm will not show the percentage
        else:
            # file size in MB
            length = round(int(content_length) / 1024**2, 2)
        if '' != head:
            os.makedirs(head, exist_ok=True)
        # remove the file left by a previous failed run, otherwise the new
        # content would be appended after the junk
        if os.path.exists(save_path):
            os.remove(save_path)
        process_bar = tqdm(
            colour='blue', total=length, unit='MB',
            desc=shorten_title(tail), initial=0)
        for part in r.iter_content(1024 ** 2):
            # update the progress bar with the real bytes downloaded, so
            # that it never exceeds 100%
            process_bar.update(len(part) / 1024**2)
            with open(save_path, 'ab') as file:
                file.write(part)
        r.close()

    # set daemon as False to continue downloading even if the main threading
    # has been killed due to KeyboardInterrupt
    t = Thread(
        target=__download, args=(urls, save_path, proxy_ip_port, cookies),
        daemon=False)
    graceful_exit.register_thread(t)
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

    def download(self, urls, save_path, time_sleep_in_seconds=5, cookies=None):
        """
        download file from given urls and save it to given path
        :param urls: str, urls
        :param save_path: str, full path
        :param time_sleep_in_seconds: int, sleep seconds after call
        :param cookies: dict or None, cookies to send with the request, e.g.
            the cookies of the logged-in browser session. Only used by the
            None|"request" downloader. Default: None.
        :return: None
        """
        # do not start new downloads after the first Ctrl+C
        if graceful_exit.is_stop_requested():
            return
        # also re-download suspiciously small files left by previous failed
        # runs (e.g. the 287-byte rate-limit error pages)
        if not is_valid_downloaded_file(save_path):
            if self.downloader is None:
                _download(
                    urls=urls,
                    save_path=save_path,
                    time_sleep_in_seconds=time_sleep_in_seconds,
                    is_random_step=self.is_random_step,
                    proxy_ip_port=self.proxy_ip_port,
                    cookies=cookies
                )
            elif self.downloader.lower() == 'idm':
                IDM.download(
                    urls=urls,
                    save_path=save_path,
                    time_sleep_in_seconds=time_sleep_in_seconds,
                    is_random_step=self.is_random_step
                )
