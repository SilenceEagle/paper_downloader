import subprocess
import os
import time

def download(urls, save_path, time_sleep_in_seconds=5):
    """
    download file from given urls and save it to given path
    :param urls: str, urls
    :param save_path: str, full path
    :param time_sleep_in_seconds: int, sleep seconds after call
    :return: None
    """
    idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'''  # should replace by the local IDM path
    basic_command = [idm_path, '/d', 'xxxx', '/p', 'xxx', '/f', 'xxxx', '/n']
    head, tail = os.path.split(save_path)
    if '' != head:
        os.makedirs(head, exist_ok=True)
    basic_command[2] = urls
    basic_command[4] = head
    basic_command[6] = tail
    p = subprocess.Popen(' '.join(basic_command))
    p.wait()
    time.sleep(time_sleep_in_seconds)


