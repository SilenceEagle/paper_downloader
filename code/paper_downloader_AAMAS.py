"""paper_downloader_AAMAS.py
"""

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

root_folder = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
from lib import csv_process
from lib.my_request import urlopen_with_retry


def save_csv(year):
    """
    write AAMAS papers' urls in one csv file
    :param year: int, AAMAS year, such 2023
    :return: peper_index: int, the total number of papers
    """
    conference = "AAMAS"
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_file_pathname = os.path.join(
        project_root_folder, 'csv', f'{conference}_{year}.csv'
    )

    init_url_dict = {
        2010: 'https://www.ifaamas.org/Proceedings/aamas2010/resources/_fullpapers.html',
        2009: 'https://www.ifaamas.org/Proceedings/aamas2009/TOC/01_FP/FP_Session.html',
        2008: 'https://www.ifaamas.org/Proceedings/aamas2008/proceedings/mainTrackPapers.htm',
    }

    error_log = []
    paper_index = 0
    with open(csv_file_pathname, 'w', newline='') as csvfile:
        fieldnames = ['title', 'group', 'main link', 'supplemental link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        if year >=  2013:
            init_url = f'https://www.ifaamas.org/Proceedings/aamas{year}' \
                f'/forms/contents.htm'
        elif year >= 2011:
            init_url = f'https://www.ifaamas.org/Proceedings/aamas{year}'\
                f'/resources/fullpapers.html'
        elif year in init_url_dict:
            init_url = init_url_dict[year]
        else:   
            # TODO: support downloading 2002 ~ 2007 papers
            return
        url_file_pathname = os.path.join(
            project_root_folder, 'urls', 
            f'init_url_{conference}_{year}.dat'''
        )
        if os.path.exists(url_file_pathname):
            with open(url_file_pathname, 'rb') as f:
                content = pickle.load(f)
        else:
            headers = {
                'User-Agent':
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'}
            content = urlopen_with_retry(url=init_url, headers=headers)
            with open(url_file_pathname, 'wb') as f:
                pickle.dump(content, f)

        soup = BeautifulSoup(content, 'html5lib')
        # soup = BeautifulSoup(content, 'html.parser')
        if year >=  2013:
            group_list = soup.find('tbody').find_all('tr', recursive=False)[3:]
            # skip "conference title", "Table of Contents" and "Contents table"  
            
            group_list_bar = tqdm(group_list)
            paper_index = 0
            is_start = False
            for group in group_list_bar:
                if not is_start:
                    # if group.find('a', {'id': 'KT'}): # year 2019, 2023, 2024
                    #     is_start = True
                    if group.find('strong'):
                        group_text = slugify(group.find('strong').text)
                        if not group_text.startswith('table') and \
                            not group_text.startswith('aamas'):  
                            # skip Table of Contents, AAMAS 20xx
                            is_start = True
                        else:
                            continue
                    else:
                        continue
                
                try:
                    tds = group.find_all('td', recursive=False)
                    if len(tds) < 2:
                        continue
                    group = tds[1]
                    papers = group.find_all('p')

                    for p in papers:
                        # group title is in <strong>...</strong>
                        if p.find('strong', recursive=False):
                            group_title = slugify(p.text)
                            continue
                        paper_dict = {'title': '',
                                    'group': group_title,
                                    'main link': '',
                                    'supplemental link': ''}
                        if p.find('a') is None and p.find('b') is None:
                            # last empty <p>...</p> in some <tr>...</tr>
                            continue
                        a = p.find('a')
                        if a is None:
                            title = slugify(p.find('b').text)
                            main_link = ''
                            print(f'\nWarning: No link found for {title}!')
                        else:
                            title = slugify(a.text)
                            main_link = urllib.parse.urljoin(init_url, a.get('href'))
                        
                        paper_dict['title'] = title
                        paper_dict['main link'] = main_link
                        paper_index += 1
                        group_list_bar.set_description_str(
                            f'Collected paper {paper_index}: {title}')
                        writer.writerow(paper_dict)
                        csvfile.flush()  # write to file immediately
                except Exception as e:
                    print(f'Warning: {str(e)}\n'
                        f'Current group: {group_title}\nCurrent paper: {title}')
        elif year >= 2010:
            class_name = {
                2010: 'plist',
                2011: 'plist',
                2012: 'pindex'
            }
            papers = soup.find('div', {'class': class_name[year]}).find_all(['h2', 'div'])
            papers_bar = tqdm(papers)
            paper_index = 0
            for p in papers_bar:
                if p.name == 'h2': # group title
                    group_title = slugify(p.text)
                else:  # div, paper
                    paper_dict = {'title': '',
                                'group': group_title,
                                'main link': '',
                                'supplemental link': ''}
                    a = p.find('span', {'class': 'title'}).find('a')
                    # title = slugify(a.find(string=True, recursive=False)) # drop abs
                    direct_text = ''.join(child for child in a.contents 
                                          if isinstance(child, str)).strip()
                    title = slugify(direct_text)
                    main_link = urllib.parse.urljoin(init_url, a.get('href'))
                    paper_dict['title'] = title
                    paper_dict['main link'] = main_link
                    paper_index += 1
                    papers_bar.set_description_str(
                        f'Collected paper {paper_index}: {title}')
                    writer.writerow(paper_dict)
                    csvfile.flush()  # write to file immediately
        elif year == 2009:
            group_list = soup.find('div', {'id': 'mainContent'}).find_all('p')
            group_list_bar = tqdm(group_list)
            paper_index = 0
            is_start = False
            for group in group_list_bar:
                if not is_start:
                    if group.find('strong'):
                        group_text = slugify(group.find('strong').text)
                        is_start = True
                    else:
                        continue
                if group.find('strong'):
                    group_title = slugify(group.text)
                    continue
                try:
                    papers = group.find_all('a')
                    for p in papers:
                        paper_dict = {'title': '',
                                    'group': group_title,
                                    'main link': '',
                                    'supplemental link': ''}
                        title = slugify(p.text)
                        main_link = urllib.parse.urljoin(init_url, p.get('href'))
                        
                        paper_dict['title'] = title
                        paper_dict['main link'] = main_link
                        paper_index += 1
                        group_list_bar.set_description_str(
                            f'Collected paper {paper_index}: {title}')
                        writer.writerow(paper_dict)
                        csvfile.flush()  # write to file immediately
                except Exception as e:
                    print(f'Warning: {str(e)}\n'
                        f'Current group: {group_title}\nCurrent paper: {title}')
        elif year == 2008:
            # papers = soup.find_all(lambda tag: 
            #     (tag.name == 'p' and 'title' in tag.get('class', [])) or 
            #     tag.name == 'a'
            # )
            group_list = soup.find('div', {'id': 'mainbody'}).find(
                'table').find('tbody').find_all('tr', recursive=False)[2:]
            # skip "conference title", "Table of Contents" 
            
            group_list_bar = tqdm(group_list)
            paper_index = 0
            for group in group_list_bar:
                
                try:
                    p_class_title = group.find('p', {'class': 'title'})
                    h3 = group.find('h3')
                    if p_class_title:                       
                        group_title = slugify(p_class_title.text)
                    elif h3:  # find <h3></h3>
                        group_title = slugify(h3.text)
                    else:
                        raise ValueError('Parse group title failed!')

                    papers = group.find_all('a')

                    for p in papers:
                        paper_dict = {'title': '',
                                    'group': group_title,
                                    'main link': '',
                                    'supplemental link': ''}
                        
                        title = slugify(p.text)
                        if not p.get('href'):
                            continue # group title
                        main_link = urllib.parse.urljoin(init_url, p.get('href'))
                        
                        paper_dict['title'] = title
                        paper_dict['main link'] = main_link
                        paper_index += 1
                        group_list_bar.set_description_str(
                            f'Collected paper {paper_index}: {title}')
                        writer.writerow(paper_dict)
                        csvfile.flush()  # write to file immediately
                except Exception as e:
                    print(f'Warning: {str(e)}\n'
                        f'Current group: {group_title}\nCurrent paper: {title}')
        else:
            # TODO: support downloading 2002 ~ 2008 papers
            return

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
    download all AAMAS paper given year
    :param year: int, AAMAS year, such as 2019
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
    conference = "AAMAS"
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
    # total_paper_number = 2021
    total_paper_number = save_csv(year)
    download_from_csv(
        year,
        save_dir=fr'D:\AAMAS_{year}',
        time_step_in_seconds=5,
        total_paper_number=total_paper_number)
    # for year in range(2008, 2025, 1):
    #     print(year)
    #     # total_paper_number = 134
    #     total_paper_number = save_csv(year)
    #     download_from_csv(year, save_dir=fr'E:\AAMAS\AAMAS_{year}',
    #                       time_step_in_seconds=10,
    #                       total_paper_number=total_paper_number)
    #     time.sleep(2)

    pass