import subprocess
import os
import time
import random


def download(urls, save_path, time_sleep_in_seconds=5, is_random_step=True,
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
    idm_path = '"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'  # should replace by the local IDM path
    basic_command = [idm_path, '/d', 'xxxx', '/p', 'xxx', '/f', 'xxxx', '/n']
    head, tail = os.path.split(save_path)
    if '' != head:
        os.makedirs(head, exist_ok=True)
    basic_command[2] = urls
    basic_command[4] = head
    basic_command[6] = tail
    p = subprocess.Popen(' '.join(basic_command))
    # p.wait()
    if is_random_step:
        time_sleep_in_seconds = random.uniform(
            0.5 * time_sleep_in_seconds,
            1.5 * time_sleep_in_seconds,
        )
    if verbose:
        print(f'\t random sleep {time_sleep_in_seconds: .2f} seconds')
    time.sleep(time_sleep_in_seconds)


