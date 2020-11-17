"""
    thunder.py
    use thunder (迅雷) to download file
    20201115
"""

from win32com.client import Dispatch
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
    path, file = os.path.split(save_path)
    thunder = Dispatch("ThunderAgent.Agent64.1")  # for thunder X
    # thunder = Dispatch("ThunderAgent.Agent.1")  # for other thunder version
    # AddTask("下载地址", "另存文件名", "保存目录","任务注释","引用地址","开始模式", "只从原始地址下载","从原始地址下载线程数")
    thunder.AddTask(urls, file, path, "", "", -1, 0, 5)
    thunder.CommitTasks()
    time.sleep(time_sleep_in_seconds)