"""paper_downloader_RSS.py
20240322"""
import time
import urllib
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import pickle
import os
from tqdm import tqdm
from slugify import slugify
import csv
import sys
from datetime import datetime

root_folder = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
from lib import csv_process
from lib.my_request import urlopen_with_retry


def get_paper_pdf_link(abs_url):
    """get paper pdf link in the abstract url.
       For newest papers that have not been added to 
       "https://www.roboticsproceedings.org/rss19/index.html"

    Args:
        abs_url (str): paper abstract page url.
    """
    headers = {
                'User-Agent':
                    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
                    'Gecko/20100101 Firefox/23.0'}
    content = urlopen_with_retry(url=abs_url, headers=headers)
    soup = BeautifulSoup(content, 'html5lib')
    paper_pdf_div = soup.find('div', {'class': 'paper-pdf'})
    paper_pdf_div = paper_pdf_div.find('a').get('href')
    return paper_pdf_div


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
        is_from_proceed = True  
        # True to get papaers from "https://www.roboticsproceedings.org"
        # False to get papers from "https://roboticsconference.org/"
        init_url = f'https://www.roboticsproceedings.org/rss' \
                   f'{year-2004 :0>2d}/index.html'
        # determine whether this year's papers had been added to 
        # "https://www.roboticsproceedings.org"
        # If not, get papers from "https://roboticsconference.org/"
        try:
            headers = {
                'User-Agent':
                    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
                    'Gecko/20100101 Firefox/23.0'}
            req = urllib.request.Request(url=init_url, headers=headers)
            urllib.request.urlopen(req, timeout=20)
        except HTTPError as e:
            if e.code == 404:  # not added
                current_year = datetime.now().year
                if year == current_year:
                    init_url = f'https://roboticsconference.org/program/papers/'
                else:
                    init_url = f'https://roboticsconference.org/{year}/program/papers/'
                is_from_proceed = False
        url_file_pathname = os.path.join(
            project_root_folder, 'urls', 
            f'init_url_{conference}_{year}_'
            f'''{'proc' if is_from_proceed else 'conf'}.dat'''
        )
        if os.path.exists(url_file_pathname):
            with open(url_file_pathname, 'rb') as f:
                content = pickle.load(f)
        else:
            headers = {
                'User-Agent':
                    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
                    'Gecko/20100101 Firefox/23.0'}
            content = urlopen_with_retry(url=init_url, headers=headers)
            with open(url_file_pathname, 'wb') as f:
                pickle.dump(content, f)

        soup = BeautifulSoup(content, 'html5lib')
        if is_from_proceed:
            paper_list = soup.find('div', {'class': 'content'}).find_all('tr')
        else:
            paper_list = soup.find('table', {'id': 'myTable'}).find_all('tr')
        paper_list_bar = tqdm(paper_list)
        paper_index = 0
        title_index = 0
        for i, paper in enumerate(paper_list_bar):
            paper_dict = {'title': '',
                          'main link': '',
                          'supplemental link': ''}
            # get title
            try:
                if not is_from_proceed and i == 0:
                    # header
                    fields = paper.find_all('th')
                    fields = [f.text.lower() for f in fields]
                    title_index = fields.index('title')
                tds = paper.find_all('td')
                if len(tds) < 2:  # seperator
                    continue
                if is_from_proceed:
                    title = slugify(tds[0].a.text)
                    main_link = tds[1].a.get('href')
                    main_link = urllib.parse.urljoin(init_url, main_link)
                else:
                    title = slugify(tds[title_index].a.text)
                    abs_link = tds[title_index].a.get('href')
                    abs_link = urllib.parse.urljoin(init_url, abs_link)
                    main_link = get_paper_pdf_link(abs_link)
                
                paper_dict['title'] = title
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
        csv_filename=None, downloader='IDM', is_random_step=True,
        proxy_ip_port=None):
    """
    download all RSS paper given year
    :param year: int, RSS year, such as 2019
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
    :param proxy_ip_port: str or None, proxy server ip address with or without
        protocol prefix, eg: "127.0.0.1:7890", "http://127.0.0.1:7890".
        Default: None
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
        is_random_step=is_random_step,
        proxy_ip_port=proxy_ip_port
    )


if __name__ == '__main__':
    year = 2025
    total_paper_number = save_csv(year)
    # total_paper_number = 134
    download_from_csv(year, save_dir=fr'E:\RSS\RSS_{year}',
                        time_step_in_seconds=15,
                        total_paper_number=total_paper_number)
    time.sleep(2)

    pass
