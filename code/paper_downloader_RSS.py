"""paper_downloader_RSS.py
20240322"""
import time
import urllib
from urllib.request import urlopen
# import time
from bs4 import BeautifulSoup
import pickle
import os
from tqdm import tqdm
from slugify import slugify
import csv
import sys
import random

root_folder = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
from lib import csv_process
from lib.user_agents import user_agents
from selenium.webdriver.common.by import By


def save_csv(year):
    """
    write RSS papers' urls in one csv file
    :param year: int, RSS year, such 2023
    :return: peper_index: int, the total number of papers
    """
    conference = "RSS"
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_file_pathname = os.path.join(
        project_root_folder, 'csv', f'{conference}_{year}.csv'
    )
    error_log = []
    paper_index = 0
    with open(csv_file_pathname, 'w', newline='') as csvfile:
        fieldnames = ['title', 'main link', 'supplemental link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        init_url = f'https://www.roboticsproceedings.org/rss' \
                   f'{year-2004 :0>2d}/index.html'
        url_file_pathname = os.path.join(
            project_root_folder, 'urls', f'init_url_{conference}_{year}.dat'
        )
        if os.path.exists(url_file_pathname):
            with open(url_file_pathname, 'rb') as f:
                content = pickle.load(f)
        else:
            headers = {
                'User-Agent':
                    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
                    'Gecko/20100101 Firefox/23.0'}
            req = urllib.request.Request(url=init_url, headers=headers)
            content = urllib.request.urlopen(req).read()
            with open(url_file_pathname, 'wb') as f:
                pickle.dump(content, f)

        soup = BeautifulSoup(content, 'html5lib')
        paper_list = soup.find('div', {'class': 'content'}).find_all('tr')
        paper_list_bar = tqdm(paper_list)
        paper_index = 0
        for paper in paper_list_bar:
            paper_dict = {'title': '',
                          'main link': '',
                          'supplemental link': ''}
            # get title
            try:
                tds = paper.find_all('td')
                if len(tds) < 2:  # seperator
                    continue
                title = slugify(tds[0].a.text)
                paper_dict['title'] = title
                main_link = tds[1].a.get('href')
                main_link = urllib.parse.urljoin(init_url, main_link)
                paper_dict['main link'] = main_link
                paper_index += 1
                paper_list_bar.set_description_str(
                    f'Collected paper {paper_index}: {title}')
                writer.writerow(paper_dict)
                csvfile.flush()  # write to file immediately
            except Exception as e:
                print(f'Warning: {str(e)}')

    #  write error log
    print('write error log')
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'download_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                if e is not None:
                    f.write(e)
                else:
                    f.write('None')
                f.write('\n')

            f.write('\n')
    return paper_index


def download_from_csv(
        year, save_dir, time_step_in_seconds=5, total_paper_number=None,
        csv_filename=None, downloader='IDM', is_random_step=True):
    """
    download all AAAI paper given year
    :param year: int, AAAI year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds
    :param total_paper_number: int, the total number of papers that is going to
        download
    :param csv_filename: None or str, the csv file's name, None means to use
        default setting
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder', default to 'IDM'
    :param is_random_step: bool, whether random sample the time step between two
        adjacent download requests. If True, the time step will be sampled
        from Uniform(0.5t, 1.5t), where t is the given time_step_in_seconds.
        Default: True.
    :return: True
    """
    conference = "RSS"
    postfix = f'{conference}_{year}'
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_file_path = os.path.join(
        project_root_folder, 'csv',
        f'{conference}_{year}.csv' if csv_filename is None else csv_filename)
    csv_process.download_from_csv(
        postfix=postfix,
        save_dir=save_dir,
        csv_file_path=csv_file_path,
        is_download_supplement=False,
        time_step_in_seconds=time_step_in_seconds,
        total_paper_number=total_paper_number,
        downloader=downloader,
        is_random_step=is_random_step
    )


if __name__ == '__main__':
    # year = 2023
    # total_paper_number = 2021
    # total_paper_number = save_csv(year)
    # download_from_csv(
    #     year,
    #     save_dir=fr'E:\AAAI_{year}',
    #     time_step_in_seconds=5,
    #     total_paper_number=total_paper_number)
    for year in range(2020, 2024, 1):
        print(year)
        # total_paper_number = None
        total_paper_number = save_csv(year)
        download_from_csv(year, save_dir=fr'E:\RSS\RSS_{year}',
                          time_step_in_seconds=7,
                          total_paper_number=total_paper_number)
        time.sleep(2)

    pass
