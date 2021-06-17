"""
paper_downloader_SIGGRAPH.py
20200817
use IDM to download all siggraph papers
"""
import urllib
from urllib.request import urlopen, Request
import time
import bs4
from bs4 import BeautifulSoup
from slugify import slugify
from lib.ACM import get_pdf_link_given_acm_abs_url
import csv
from tqdm import tqdm
import os
import subprocess


def get_paper_detail_from_paperlist_page(paper_list_url):
    """
    get the all papers' session name, title and abs link from paper list url
    :param paper_list_url:
    :return:
    """
    r = Request(paper_list_url, headers={'User-Agent': 'Mozilla/5.0'})
    content = urlopen(r).read()
    soup = BeautifulSoup(content, 'html5lib')
    papers = soup.find('div', {'id': 'DLcontent'}).find_all(['h2', 'h3'])
    session_title_absurl = []
    session = ''
    for h in papers:
        title = ''
        abs_url = ''
        if 'h2' == h.name:
            session = slugify(h.text)
        else:  # h3
            title = slugify(h.text)
            abs_url = h.a.get('href')
            abs_url = urllib.parse.urljoin(paper_list_url, abs_url)
            session_title_absurl.append([session, title, abs_url])
    return session_title_absurl


def get_paperlisturl_from_content_page(content_page_url):
    """
    get the paperlist name and url from content page url
    :param content_page_url:
    :return: list, each item is a list of [conference_name, paperlist_name, url]
    """
    r = Request(content_page_url, headers={'User-Agent': 'Mozilla/5.0'})
    content = urlopen(r).read()
    soup = BeautifulSoup(content, 'html5lib')
    content = soup.find('div', {'class': 'entry-content'}).find_all(['h3', 'ul'])
    conference_paperlist_url = []
    conference_name = ''
    for c in content:
        if 'h3' == c.name and c.text.startswith('SIGGRAPH'):
            conference_name = c.text
        elif conference_name != '':  # ul
            for li in c.find_all('li'):
                if li.a.text.startswith('Open Access'):
                    paperlist_name = li.a.text
                    paperlist_url = li.a.get('href')
                    paperlist_url = urllib.parse.urljoin(content_page_url, paperlist_url)
                    conference_paperlist_url.append([conference_name, paperlist_name, paperlist_url])
    return conference_paperlist_url


def save_csv(year, is_asia=False):
    """
    get SIGGRAPH paper's group, session, title and url and save to csv file
    :param year:
    :return:
    """
    error_log = []
    cvs_file_name = f'..\\csv\\SIGGRAPH_{year}.csv' if not is_asia else f'..\\csv\\SIGGRAPH_Asia_{year}.csv'
    with open(cvs_file_name, 'w', newline='') as csvfile:
        fieldnames = ['title', 'link', 'session', 'group', 'conference']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        content_page_url = 'https://www.siggraph.org/learn/conference-content/'
        conference_paperlist_url = get_paperlisturl_from_content_page(content_page_url)
        # try:
        pbar = tqdm(conference_paperlist_url)
        paper_ind = 0
        for conference in pbar:
            conf_name = slugify(conference[0])
            if is_asia and -1 == conf_name.find('asia'):
                continue
            if not is_asia and -1 != conf_name.find('asia'):
                continue
            pbar.set_description(f'processing {conf_name}')
            if -1 != conf_name.find(str(year)):
                group = slugify(conference[1])
                session_title_absurl = get_paper_detail_from_paperlist_page(conference[2])
                for paper in session_title_absurl:
                    paper_ind += 1
                    paper_dict = {
                        'conference': conf_name,
                        'group': group,
                        'session': slugify(paper[0]),
                        'title': slugify(paper[1]),
                        'link': get_pdf_link_given_acm_abs_url(paper[2])}
                    writer.writerow(paper_dict)
                    print(f'paper {paper_ind}: {slugify(paper[1])}')
                    time.sleep(2)
        # except Exception as e:
        #     print(e)
        #     error_log.append(e)


def download_from_csv(
        year, save_dir, time_step_in_seconds=5, total_paper_number=None, is_asia=False):
    """
    download all SIGGRAPH paper and supplement files given year, restore in save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, SIGGRAPH year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental material
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :param total_paper_number: int, the total number of papers that is going to download
    :param is_asia: bool, is to download workshops from csv file.
    :return: True
    """
    # use IDM to download everything
    idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'''  # should replace by the local IDM path
    basic_command = [idm_path, '/d', 'xxxx', '/p', 'xxx', '/f', 'xxxx', '/n']

    error_log = []
    postfix = f'SIGGRAPH_{year}' if not is_asia else f'SIGGRAPH_Asia_{year}'

    csv_file_name = f'..\\csv\\SIGGRAPH_{year}.csv' if not is_asia else f'..\\csv\\SIGGRAPH_Asia_{year}.csv'
    with open(csv_file_name, newline='') as csvfile:
        myreader = csv.DictReader(csvfile, delimiter=',')
        pbar = tqdm(myreader)
        i = 0
        for this_paper in pbar:
            i += 1
            # get title
            group = this_paper['group']
            title = this_paper['title']
            session = this_paper['session']
            link = this_paper['link']
            conference = this_paper['conference']
            if is_asia and -1 == slugify(conference).find('asia'):
                continue
            if total_paper_number is not None:
                pbar.set_description(f'Downloading paper {i}/{total_paper_number}')

            else:
                pbar.set_description(f'Downloading paper {i}')

            this_paper_main_path = save_dir
            if conference != '':
                this_paper_main_path = os.path.join(this_paper_main_path, slugify(conference))
                if group != '':
                    this_paper_main_path = os.path.join(this_paper_main_path, slugify(group))
                    if session != '':
                        this_paper_main_path = os.path.join(this_paper_main_path, slugify(session))

            this_paper_main_path = os.path.join(this_paper_main_path, f'{title}_{postfix}.pdf')
            if os.path.exists(this_paper_main_path):
                    continue
            if '' == link:
                error_log.append((conference, group, title, 'no link'))
            else:
                try:
                    # download paper with IDM
                    if not os.path.exists(this_paper_main_path):
                        head, tail = os.path.split(this_paper_main_path)
                        os.makedirs(head, exist_ok=True)
                        basic_command[2] = link.replace(' ', '%20')
                        basic_command[4] = head
                        basic_command[6] = tail
                        p = subprocess.Popen(' '.join(basic_command))
                        p.wait()
                        time.sleep(time_step_in_seconds if time_step_in_seconds >= 5 else 5)
                        # while True:
                        #     if os.path.exists(this_paper_main_path):
                        #         break
                except Exception as e:
                    # error_flag = True
                    print('Error: ' + title + ' - ' + str(e))
                    error_log.append((conference, group, title, link, 'main paper download error', str(e)))

        # 2. write error log
        print('write error log')
        with open('..\\log\\download_err_log.txt', 'w') as f:
            for log in tqdm(error_log):
                for e in log:
                    if e is not None:
                        f.write(e)
                    else:
                        f.write('None')
                    f.write('\n')

                f.write('\n')

if __name__ == '__main__':
    # paper_list_url = 'https://www.siggraph.org/wp-content/uploads/2020/01/SA-19-Art-Gallery-Art-Papers.html'
    # get_paper_detail_from_paperlist_page(paper_list_url)
    # content_page_url = 'https://www.siggraph.org/learn/conference-content/'
    # get_paperlisturl_from_content_page(content_page_url)
    year = 2019
    is_asia = False
    save_csv(2019, is_asia)
    download_from_csv(
        year,
        save_dir=r'F:\SIGGRAPH',
        time_step_in_seconds=60,
        total_paper_number=None,
        is_asia=is_asia)
