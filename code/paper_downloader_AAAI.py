"""paper_downloader_AAAI.py"""
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


def get_track_urls(year):
    """
    get all the technical tracks urls given AAAI proceeding year
    Args:
        year (int): AAAI proceeding year, such 2023

    Returns:
        dict : All the urls of technical tracks included in
            the given AAAI proceeding. Keys are the tracks name-volume,
            and values are the corresponding urls.
    """
    # assert int(year) >= 2023, f"only support year >= 2023, but get {year}!!!"
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dat_file_pathname = os.path.join(
        project_root_folder, 'urls', f'track_archive_url_AAAI_{year}.dat'
    )
    proceeding_th_dict = {
        1980: 1,
        1902: 2,
        1983: 3,
        1984: 4,
        1986: 5,
        1987: 6,
        1988: 7,
        1990: 8,
        1991: 9,
        1992: 10,
        1993: 11,
        1994: 12,
        1996: 13,
        1997: 14,
        1998: 15,
        1999: 16,
        2000: 17,
        2002: 18,
        2004: 19,
        2005: 20,
        2006: 21,
        2007: 22,
        2008: 23
    }
    if year >= 2023:
        base_url = r'https://ojs.aaai.org/index.php/AAAI/issue/archive'
        headers = {
            'User-Agent': user_agents[-1],
            'Host': 'ojs.aaai.org',
            'Referer': "https://ojs.aaai.org",
            'GET': base_url
        }
        if os.path.exists(dat_file_pathname):
            with open(dat_file_pathname, 'rb') as f:
                content = pickle.load(f)
        else:
            req = urllib.request.Request(url=base_url, headers=headers)
            content = urllib.request.urlopen(req).read()
            # content = open(f'..\\AAAI_{year}.html', 'rb').read()
            with open(dat_file_pathname, 'wb') as f:
                pickle.dump(content, f)
        soup = BeautifulSoup(content, 'html5lib')
        tracks = soup.find('ul', {'class': 'issues_archive'}).find_all('li')
        track_urls = dict()
        for tr in tracks:
            h2 = tr.find('h2')
            this_track = slugify(h2.a.text)
            if this_track.startswith(f'aaai-{year-2000}'):
                this_track += slugify(h2.div.text) + '-' + this_track
                this_url = h2.a.get('href')
                track_urls[this_track] = this_url
                print(f'find track: {this_track}({this_url})')
    else:
        if year >= 2010:
            proceeding_th = year - 1986
        elif year in proceeding_th_dict:
            proceeding_th = proceeding_th_dict[year]
        else:
            print(f'ERROR: AAAI proceeding was not held in year {year}!!!')
            return

        base_url = f'https://aaai.org/proceeding/aaai-{proceeding_th:02d}-{year}/'
        headers = {
            'User-Agent': user_agents[-1],
            'Host': 'aaai.org',
            'Referer': "https://aaai.org",
            'GET': base_url
        }
        if os.path.exists(dat_file_pathname):
            with open(dat_file_pathname, 'rb') as f:
                content = pickle.load(f)
        else:
            req = urllib.request.Request(url=base_url, headers=headers)
            content = urllib.request.urlopen(req).read()
            # content = open(f'..\\AAAI_{year}.html', 'rb').read()
            with open(dat_file_pathname, 'wb') as f:
                pickle.dump(content, f)
        soup = BeautifulSoup(content, 'html5lib')
        tracks = soup.find('main', {'class': 'content'}).find_all('li')
        track_urls = dict()
        for tr in tracks:
            this_track = slugify(tr.a.text)
            this_url = tr.a.get('href')
            track_urls[this_track] = this_url
            print(f'find track: {this_track}({this_url})')
    return track_urls


def get_papers_of_track_ojs(track_url):
    """
    get all the papers' title, belonging track group name and download link.
    the link should be hosted on https://ojs.aaai.org/
    Args:
        track_url (str): track url

    Returns:
        list[dict]: a list contains all the collected papers' information,
            each item in list is a dictionary, whose keys include
            ['title', 'main link', 'group']
            And the group is the specific track name.
    """
    debug = False
    paper_list = []
    headers = {
        'User-Agent': user_agents[-1],
        'Host': 'ojs.aaai.org',
        'Referer': "https://ojs.aaai.org",
        'GET': track_url
    }
    req = urllib.request.Request(url=track_url, headers=headers)
    content = urllib.request.urlopen(req).read()
    soup = BeautifulSoup(content, 'html5lib')
    tracks = soup.find('div', {'class': 'sections'}).find_all(
        'div', {'class': 'section'})
    for tr in tracks:
        this_group = slugify(tr.h2.text)
        this_paper_dict = {
            'group': this_group,
            'title': '',
            'main link': ''
        }
        papers = tr.find_all('li')
        for p in papers:
            this_paper_dict['title'] = ''
            this_paper_dict['main link'] = ''
            try:
                title = slugify(p.find('h3', {'class': 'title'}).text)
                link = p.find(
                    'a', {'class': 'obj_galley_link pdf'}
                ).get('href').replace('view', 'download')
                this_paper_dict['title'] = title
                this_paper_dict['main link'] = link
                paper_list.append(this_paper_dict.copy())
                if debug:
                    print(
                        f'paper: {title}\n\tlink:{link}\n\tgroup:{this_group}')
            except Exception as e:
                # skip unwanted target
                # print(f'ERROR: {str(e)}')
                pass
                # continue

    return paper_list


def get_papers_of_track(track_url):
    """
    get all the papers' title, belonging track group name and download link.
    the link should be hosted on https://.aaai.org/
    Args:
        track_url (str): track url

    Returns:
        list[dict]: a list contains all the collected papers' information,
            each item in list is a dictionary, whose keys include
            ['title', 'main link', 'group']
            And the group is the specific track name.
    """
    debug = False
    paper_list = []
    headers = {
        'User-Agent': user_agents[-1],
        'Host': 'aaai.org',
        'Referer': "https://aaai.org",
        'GET': track_url
    }
    req = urllib.request.Request(url=track_url, headers=headers)
    content = urllib.request.urlopen(req).read()
    soup = BeautifulSoup(content, 'html5lib')
    tracks = soup.find('main', {'id': 'genesis-content'}).find_all(
        'div', {'class': 'track-wrap'})
    for tr in tracks:
        this_group = slugify(tr.h2.text)
        this_paper_dict = {
            'group': this_group,
            'title': '',
            'main link': ''
        }
        papers = tr.find_all('li')
        for p in papers:
            this_paper_dict['title'] = ''
            this_paper_dict['main link'] = ''
            try:
                title = slugify(p.find('h5').text)
                link = p.find(
                    'a', {'class': 'wp-block-button'}
                ).get('href')
                this_paper_dict['title'] = title
                this_paper_dict['main link'] = link
                paper_list.append(this_paper_dict.copy())
                if debug:
                    print(
                        f'paper: {title}\n\tlink:{link}\n\tgroup:{this_group}')
            except Exception as e:
                # skip unwanted target
                # print(f'ERROR: {str(e)}')
                pass
                # continue

    return paper_list


def save_csv(year):
    """
    write AAAI papers' urls in one csv file
    :param year: int, AAAI year, such 2019
    :return: peper_index: int, the total number of papers
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_file_pathname = os.path.join(
        project_root_folder, 'csv', f'AAAI_{year}.csv'
    )
    error_log = []
    paper_index = 0
    with open(csv_file_pathname, 'w', newline='') as csvfile:
        fieldnames = ['title', 'main link', 'group']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        track_urls = get_track_urls(year)
        for tr_name in track_urls:
            tr_url = track_urls[tr_name]
            print(f'collecting paper from {tr_name}({tr_url})')
            for r in range(3):
                try:
                    if year >= 2023:
                        papers_dict_list = get_papers_of_track_ojs(tr_url)
                    else:
                        papers_dict_list = get_papers_of_track(tr_url)
                    break
                except Exception as e:
                    print(f'WARING: {str(e)}')
                    s = random.randint(3, 7)
                    print(f'random sleeping {s} seconds and doing {r+1}-th '
                          f'retrying...')
                    time.sleep(
                        random.randint(3, 7))  # avoid requesting too frequently
            print(f'\tfind {len(papers_dict_list)} papers')
            for p in papers_dict_list:
                paper_index += 1
                writer.writerow(p)
            csvfile.flush()
            s = random.randint(3, 7)
            print(f'random sleeping {s} seconds...')
            time.sleep(s)  # avoid requesting too frequently

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


# def save_csv(year):
#     """
#     write AAAI papers' urls in one csv file
#     :param year: int, AAAI year, such 2019
#     :return: peper_index: int, the total number of papers
#     """
#     project_root_folder = os.path.abspath(
#         os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#     csv_file_pathname = os.path.join(
#         project_root_folder, 'csv', f'AAAI_{year}.csv'
#     )
#     with open(csv_file_pathname, 'w', newline='') as csvfile:
#         fieldnames = ['title', 'main link', 'group']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()
#         if year >= 2010:
#             init_url = f'https://www.aaai.org/ocs/index.php/AAAI/' \
#                        f'AAAI{year - 2000}/schedConf/presentations'
#         elif year >= 2000:
#             init_url = f'https://www.aaai.org/Library/AAAI/' \
#                        f'aaai0{year - 2000}contents.php'
#         else:
#             init_url = f'https://www.aaai.org/Library/AAAI/' \
#                        f'aaai{year - 1900}contents.php'
#         # create current dict
#         error_log = []
#         # paper_dict = dict()
#
#         postfix = f'AAAI_{year}'
#         dat_file_pathname = os.path.join(
#             project_root_folder, 'urls', f'init_url_AAAI_{year}.dat'
#         )
#         if os.path.exists(dat_file_pathname):
#             with open(dat_file_pathname, 'rb') as f:
#                 content = pickle.load(f)
#         else:
#             content = urlopen(init_url).read()
#             # content = open(f'..\\AAAI_{year}.html', 'rb').read()
#             with open(dat_file_pathname, 'wb') as f:
#                 pickle.dump(content, f)
#         soup = BeautifulSoup(content, 'html5lib')
#         paper_index = 0
#         if year >= 2010:
#             div_content = soup.find('div', {'id': 'content'})
#             pbar = tqdm(div_content.find_all(['h4', 'table']))
#             for child in pbar:
#                 if 'h4' == child.name:  # group name
#                     this_group = slugify(child.text)
#                 else:  # table
#                     link = None
#                     try:
#                         all_as = child.find_all('a')
#                         title = slugify(all_as[0].text)
#                     except Exception as e:
#                         pass
#                     try:
#                         for a in all_as:
#                             if a.text == 'PDF':
#                                 link = a.get('href').replace('view', 'download')
#                                 paper_dict = {'title': title,
#                                               'main link': link,
#                                               'group': this_group}
#                                 paper_index += 1
#                                 pbar.set_description(
#                                     f'downloading paper: {title}')
#                                 # print(f'downloading paper: {title}')
#                                 # print(link)
#                                 writer.writerow(paper_dict)
#                     except Exception as e:
#                         print('Error: ' + title + ' - ' + str(e))
#                         if link is None:
#                             paper_dict = {'title': title,
#                                           'main link': 'error',
#                                           'group': this_group}
#                             error_log.append((title, 'error', str(e)))
#                         else:
#                             paper_dict = {'title': title,
#                                           'main link': link,
#                                           'group': this_group}
#                         paper_index += 1
#                         writer.writerow(paper_dict)
#         else:
#             paper_list_bar = tqdm(
#                 soup.find('div', {'id': 'content'}).find_all(['h3', 'h4', 'p']))
#             this_group = ''
#             for paper in paper_list_bar:
#                 if 'h3' == paper.name:  # group h3
#                     this_group_v3 = slugify(paper.text.strip())
#                     this_group = this_group_v3
#                 elif 'h4' == paper.name:  # group h4
#                     this_group_v4 = slugify(paper.text.strip())
#                     this_group = this_group_v3 + '--' + this_group_v4
#                 else:  # paper
#                     # get title and link
#                     title = None
#                     link = None
#                     all_as = paper.find_all('a')
#                     if len(all_as) >= 1:
#                         for a in all_as:
#                             abs_link = a.get('href')
#                             if abs_link is not None:
#                                 abs_link = urllib.parse.urljoin(init_url,
#                                                                 abs_link)
#                                 title = slugify(a.text.strip())
#                                 if 'pdf' == abs_link[-3:]:
#                                     link = abs_link
#                                     break
#                                 else:
#                                     headers = {
#                                         'User-Agent':
#                                             'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
#                                     req = urllib.request.Request(url=abs_link,
#                                                                  headers=headers)
#                                     for i in range(3):
#                                         try:
#                                             abs_content = urllib.request.urlopen(
#                                                 req, timeout=10).read()
#                                             break
#                                         except:
#                                             pass
#                                     if abs_content is not None:
#                                         abs_soup = BeautifulSoup(abs_content,
#                                                                  'html5lib')
#                                         h1 = abs_soup.find('h1')
#                                         try:
#                                             link = urllib.parse.urljoin(
#                                                 abs_link, h1.a.get('href')[8:])
#                                         except:
#                                             break
#                                         if link is not None:
#                                             break
#                     if title is not None:
#                         paper_index += 1
#                         paper_list_bar.set_description_str(
#                             f'Downloading paper {paper_index}: {title}')
#                         if title is not None:
#                             paper_dict = {'title': title,
#                                           'main link': link,
#                                           'group': this_group}
#                         else:
#                             paper_dict = {'title': title,
#                                           'main link': 'error',
#                                           'group': this_group}
#                             error_log.append((title, 'no link'))
#                         writer.writerow(paper_dict)
#
#         #  write error log
#         print('write error log')
#         log_file_pathname = os.path.join(
#             project_root_folder, 'log', 'download_err_log.txt'
#         )
#         with open(log_file_pathname, 'w') as f:
#             for log in tqdm(error_log):
#                 for e in log:
#                     if e is not None:
#                         f.write(e)
#                     else:
#                         f.write('None')
#                     f.write('\n')
#
#                 f.write('\n')
#     return paper_index


# def save_csv_given_urls(urls, csv_filename='AAAI_tmp.csv'):
#     """
#     write IJCAI papers' urls in one csv file
#     :param urls: str, the urls of paper website, such as
#         'https://www.aaai.org/Library/AAAI/aaai20contents-issue01.php'
#     :param csv_filename: str, csv file's name, default to 'AAAI_tmp.csv'
#     :return: peper_index: int, the total number of papers
#     """
#     project_root_folder = os.path.abspath(
#         os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#     csv_file_pathname = os.path.join(
#         project_root_folder, 'csv', csv_filename
#     )
#     if os.path.exists(csv_file_pathname):
#         print(f'''found local csv file: {csv_file_pathname}''')
#         return None
#     with open(csv_file_pathname, 'w', newline='') as csvfile:
#         fieldnames = ['title', 'main link', 'group']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()
#
#         content = urlopen(urls).read()
#         paper_index = 0
#         soup = BeautifulSoup(content, 'html5lib')
#         error_log = []
#         pbar = tqdm(
#             soup.find('div', {'class': 'content'}).find_all(['a', 'h4', 'p']))
#         this_group = ''
#         for paper in pbar:
#             if 'a' == paper.name:
#                 if paper.get('name') is not None:
#                     this_group = slugify(paper.text)
#             elif 'h4' == paper.name:
#                 this_group = slugify(paper.text)
#             else:
#                 paper_index += 1
#                 all_a = paper.find_all('a')
#                 title = slugify(all_a[0].text)
#                 pbar.set_description(
#                     f'downloading paper {paper_index}: {title}')
#                 is_get_link = False
#                 if 'pdf' == slugify(all_a[1].text):
#                     link = urllib.parse.urljoin(urls, all_a[1].get('href'))
#                     is_get_link = True
#                 if is_get_link:
#                     paper_dict = {'title': title,
#                                   'main link': link,
#                                   'group': this_group}
#                 else:
#                     paper_dict = {'title': title,
#                                   'main link': 'error',
#                                   'group': this_group}
#                     print(f'get link for {title} failed!')
#                     error_log.apend(title, 'no link')
#                 writer.writerow(paper_dict)
#         #  write error log
#         print('write error log')
#         log_file_pathname = os.path.join(
#             project_root_folder, 'log', 'download_err_log.txt')
#         with open(log_file_pathname, 'w') as f:
#             for log in tqdm(error_log):
#                 for e in log:
#                     if e is not None:
#                         f.write(e)
#                     else:
#                         f.write('None')
#                     f.write('\n')
#
#                 f.write('\n')
#
#     return paper_index if paper_index is not None else None


def download_from_csv(
        year, save_dir, time_step_in_seconds=5, total_paper_number=None,
        csv_filename=None, downloader='IDM'):
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
    :return: True
    """
    postfix = f'AAAI_{year}'
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_file_path = os.path.join(
        project_root_folder, 'csv',
        f'AAAI_{year}.csv' if csv_filename is None else csv_filename)
    csv_process.download_from_csv(
        postfix=postfix,
        save_dir=save_dir,
        csv_file_path=csv_file_path,
        is_download_supplement=False,
        time_step_in_seconds=time_step_in_seconds,
        total_paper_number=total_paper_number,
        downloader=downloader
    )


if __name__ == '__main__':
    year = 2023
    # total_paper_number = 2022
    total_paper_number = save_csv(year)
    download_from_csv(year, save_dir=f'..\\AAAI_{year}',
                      time_step_in_seconds=5,
                      total_paper_number=total_paper_number)
    # for year in range(2012, 2018, 2):
    #     print(year)
    #     total_paper_number = None
    #     # total_paper_number = save_csv(year)
    #     download_from_csv(year, save_dir=f'..\\AAAI_{year}',
    #                       time_step_in_seconds=10,
    #                       total_paper_number=total_paper_number)
    #     time.sleep(2)
    # for i in range(1, 12):
    #     print(f'issue {i}/{11}')
    #     year = 2022
    #     total_paper_number = save_csv_given_urls(
    #         urls=f'https://www.aaai.org/Library/AAAI/aaai{year - 2000}-issue{i:0>2}.php',
    #         csv_filename=f'.\AAAI_{year}_issue_{i}.csv'
    #     )
    #     # total_paper_number = 156
    #     download_from_csv(
    #         year=year,
    #         csv_filename=f'.\AAAI_{year}_issue_{i}.csv',
    #         save_dir=rf'D:\AAAI_{year}',
    #         time_step_in_seconds=1,
    #         total_paper_number=total_paper_number)

    # print(get_track_urls(1980))
    # get_papers_of_track(r'https://ojs.aaai.org/index.php/AAAI/issue/view/548')

    pass
