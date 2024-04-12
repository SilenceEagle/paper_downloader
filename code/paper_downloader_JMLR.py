"""paper_downloader_JMLR.py"""

import urllib
from bs4 import BeautifulSoup
import pickle
import os
from tqdm import tqdm
from slugify import slugify
import time
import sys
root_folder = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
from lib.downloader import Downloader
from lib.my_request import urlopen_with_retry


def download_paper(
        volumn, save_dir, time_step_in_seconds=5, downloader='IDM', url=None,
        is_use_url=False, refresh_paper_list=True):
    """
    download all JMLR paper files given volumn and restore in save_dir
    respectively
    :param volumn: int, JMLR volumn, such as 2019
    :param save_dir: str, paper and supplement material's saving path
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :param downloader: str, the downloader to download, could be 'IDM' or 'Thunder', default to 'IDM'
    :param url: None or str, None means to download volumn papers.
    :param is_use_url: bool, if to download papers from 'url'. url couldn't be None when is_use_url is True.
    :param refresh_paper_list: bool, if to refresh the saved paper list, default
        true, which means the "dat" file that contains the papers' information
        will be re-downloaded.
    :return: True
    """
    downloader = Downloader(downloader=downloader)
    # create current dict
    title_list = []
    # paper_dict = dict()
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
    if not is_use_url:
        init_url = f'http://jmlr.org/papers/v{volumn}/'
        postfix = f'JMLR_v{volumn}'
        dat_file_pathname = os.path.join(
            project_root_folder, 'urls', f'init_url_JMLR_v{volumn}.dat')
        if not refresh_paper_list and \
                os.path.exists(dat_file_pathname):
            with open(dat_file_pathname, 'rb') as f:
                content = pickle.load(f)
        else:
            print('collecting papers from website...')
            content = urlopen_with_retry(url=init_url, headers=headers)
            # content = open(f'..\\JMLR_{volumn}.html', 'rb').read()
            with open(dat_file_pathname, 'wb') as f:
                pickle.dump(content, f)
    elif url is not None:
        content = urlopen_with_retry(url=url, headers=headers)
        postfix = f'JMLR'
    else:
        raise ValueError(''''url' could not be None when 'is_use_url'=True!!!''')
    # soup = BeautifulSoup(content, 'html.parser')
    soup = BeautifulSoup(content, 'html5lib')
    # soup = BeautifulSoup(open(r'..\JMLR_2011.html', 'rb'), 'html.parser')
    error_log = []
    os.makedirs(save_dir, exist_ok=True)

    if (not is_use_url) and volumn <= 4:
        paper_list = soup.find('div', {'id': 'content'}).find_all('tr')
    else:
        paper_list = soup.find('div', {'id': 'content'}).find_all('dl')
    # num_download = 5 # number of papers to download
    num_download = len(paper_list)
    print(f'total papers counting: {num_download}, start downloading...')
    for paper in tqdm(zip(paper_list, range(num_download))):
        # get title
        this_paper = paper[0]
        title = slugify(this_paper.find('dt').text)
        title_list.append(title)

        this_paper_main_path = os.path.join(save_dir, f'{title}_{postfix}.pdf'.replace(' ', '_'))
        if os.path.exists(this_paper_main_path):
            continue

        # get abstract page url
        links = this_paper.find_all('a')
        main_link = None
        for link in links:
            if '[pdf]' == link.text or 'pdf' == link.text:
                main_link = urllib.parse.urljoin('http://jmlr.org', link.get('href'))
                break

        # try 1 time
        # error_flag = False
        for d_iter in range(1):
            try:
                # download paper with IDM
                if not os.path.exists(this_paper_main_path) and main_link is not None:
                    try:
                        print('Downloading paper {}/{}: {}'.format(paper[1] + 1, num_download, title))
                    except:
                        print(title.encode('utf8'))
                    downloader.download(
                        urls=main_link,
                        save_path=this_paper_main_path,
                        time_sleep_in_seconds=time_step_in_seconds
                    )
            except Exception as e:
                # error_flag = True
                print('Error: ' + title + ' - ' + str(e))
                error_log.append((title, main_link, 'main paper download error', str(e)))

    # store the results
    # 1. store in the pickle file
    # with open(f'{postfix}_pre.dat', 'wb') as f:
    #     pickle.dump(paper_dict, f)

    # 2. write error log
    print('write error log')
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'download_err_log.txt')
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                if e is not None:
                    f.write(e)
                else:
                    f.write('None')
                f.write('\n')

            f.write('\n')


def download_special_topics_and_issues_paper(save_dir, time_step_in_seconds=5, downloader='IDM'):
    """
    download all JMLR special topics and issues paper files given volumn and restore in save_dir
    respectively
    :param save_dir: str, paper and supplement material's saving path
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :param downloader: str, the downloader to download, could be 'IDM' or 'Thunder', default to 'IDM'
    :return: True
    """
    homepage = 'https://www.jmlr.org/papers/'
    headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
    # postfix = f'JMLR_v{volumn}'

    content = urlopen_with_retry(url=homepage, headers=headers)
    soup = BeautifulSoup(content, 'html5lib')
    # soup = BeautifulSoup(open(r'..\JMLR_2011.html', 'rb'), 'html.parser')

    all_topics = soup.find('div', {'id': 'content'}).find_all(['h2', 'p'])
    is_topic = False
    is_issue = False
    for topic in all_topics:
        if 'h2' == topic.name and slugify(topic.text.strip()) == 'special-topics':
            is_topic = True
        elif 'h2' == topic.name:
            is_topic = False
            if 'special-issues' == slugify(topic.text.strip()):
                is_issue = True
        if is_topic and 'p' == topic.name:
            topic_name = slugify(topic.text.strip())
            topic_url = urllib.parse.urljoin(homepage, topic.a.get('href'))
            # print(f'T: {topic_name} url:{topic_url}')
            print(f'processing special topic: {topic_name}')
            download_paper(
                volumn=1000,
                save_dir=os.path.join(save_dir, 'special-topics', topic_name),
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                url=topic_url,
                is_use_url=True
            )
            time.sleep(time_step_in_seconds)
        if is_issue and 'p' == topic.name:
            issue_name = slugify(topic.text.strip())
            issue_url = urllib.parse.urljoin(homepage, topic.a.get('href'))
            # print(f'T: {issue_name} url:{issue_url}')
            print(f'processing special issue: {issue_name}')
            download_paper(
                volumn=1000,
                save_dir=os.path.join(save_dir, 'special-issues', issue_name),
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                url=issue_url,
                is_use_url=True
            )
            time.sleep(time_step_in_seconds)


if __name__ == '__main__':
    volumn = 25
    download_paper(volumn, rf'W:\all_papers\JMLR\JMLR_v{volumn}',
                   time_step_in_seconds=3)
    # download_special_topics_and_issues_paper(
    #     rf'Z:\all_papers\JMLR', time_step_in_seconds=3, downloader='IDM')
    pass
