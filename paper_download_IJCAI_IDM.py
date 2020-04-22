"""paper_download_IJCAI_IDM.py"""

import urllib
from urllib.request import urlopen
import time
import bs4
from bs4 import BeautifulSoup
import pickle
# from PyPDF2 import PdfFileMerger
from PyPDF3 import PdfFileMerger
import zipfile
import os
import shutil
from tqdm import tqdm
import subprocess
from slugify import slugify
import csv


def save_csv(year):
    """
    write IJCAI papers' urls in one csv file
    :param year: int, IJCAI year, such 2019
    :return: True
    """
    with open(f'IJCAI_{year}.csv', 'w', newline='') as csvfile:
        fieldnames = ['title', 'link', 'group']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        if year >= 2003:
            init_urls = [f'https://www.ijcai.org/Proceedings/{year}/']
        elif year >= 1977:
            init_urls = [f'https://www.ijcai.org/Proceedings/{year}-1/',
                         f'https://www.ijcai.org/Proceedings/{year}-2/']
        elif year >= 1969:
            init_urls = [f'https://www.ijcai.org/Proceedings/{year}/']
        else:
            raise ValueError('invalid year!')
        error_log = []
        if len(init_urls) == 1:
            if os.path.exists(f'.\\init_url_IJCAI_{year}.dat'):
                with open(f'.\\init_url_IJCAI_{year}.dat', 'rb') as f:
                    content = pickle.load(f)
            else:
                content = urlopen(init_urls[0]).read()
                with open(f'.\\init_url_IJCAI_{year}.dat', 'wb') as f:
                    pickle.dump(content, f)
            contents = [content]
        else:
            contents = []
            if os.path.exists(f'.\\init_url_IJCAI_0_{year}.dat'):
                with open(f'.\\init_url_IJCAI_0_{year}.dat', 'rb') as f:
                    content = pickle.load(f)
            else:
                content = urlopen(init_urls[0]).read()
                with open(f'.\\init_url_IJCAI_0_{year}.dat', 'wb') as f:
                    pickle.dump(content, f)
            contents.append(content)
            if os.path.exists(f'.\\init_url_IJCAI_1_{year}.dat'):
                with open(f'.\\init_url_IJCAI_1_{year}.dat', 'rb') as f:
                    content = pickle.load(f)
            else:
                content = urlopen(init_urls[1]).read()
                with open(f'.\\init_url_IJCAI_1_{year}.dat', 'wb') as f:
                    pickle.dump(content, f)
            contents.append(content)
        for content in contents:
            soup = BeautifulSoup(content, 'html5lib')
            paper_index = 0
            if year >= 2017:
                pbar = tqdm(soup.find_all('div', {'class': 'section_title'}))
                for section in pbar:
                    this_group = slugify(section.text)
                    papers = section.parent.find_all('div', {'class': 'paper_wrapper'})
                    for paper in papers:
                        paper_index += 1
                        is_get_link = False
                        title = slugify(paper.find('div', {'class': 'title'}).text)
                        pbar.set_description(f'downloading paper {paper_index}: {title}')
                        for a in paper.find('div', {'class': 'details'}).find_all('a'):
                            if 'PDF' == a.text:
                                link = init_urls[0] + a.get('href')
                                is_get_link = True
                                break
                        if is_get_link:
                            paper_dict = {'title': title,
                                          'link': link,
                                          'group': this_group}
                        else:
                            paper_dict = {'title': title,
                                          'link': 'error',
                                          'group': this_group}
                            print(f'get link for {title}_{year} failed!')
                            error_log.apend(title, 'no link')
                        writer.writerow(paper_dict)
            elif year in [2016]:  # no group
                papers_bar = tqdm(soup.find_all('p'))
                for paper in papers_bar:
                    all_as = paper.find_all('a')
                    if len(all_as) >= 2:  # paper pdf and abstract
                        paper_index += 1
                        title = slugify(paper.text.split('\n')[0])
                        papers_bar.set_description(f'downloading paper {paper_index}: {title}')
                        is_get_link = False
                        for a in all_as:
                            if 'PDF' == a.text:
                                link = 'https://www.ijcai.org' + a.get('href')
                                is_get_link = True
                                break
                        if is_get_link:
                            paper_dict = {'title': title,
                                          'link': link,
                                          'group': ''}
                        else:
                            paper_dict = {'title': title,
                                          'link': 'error',
                                          'group': ''}
                            print(f'get link for {title}_{year} failed!')
                            error_log.apend(title, 'no link')
                        writer.writerow(paper_dict)
            elif year in [2015]:  # p group 'PDF'
                div_content = soup.find('div', {'id': 'content'})
                papers_bar = tqdm(div_content.find_all(['h2', 'p', 'h3']))
                is_start = False
                this_group = ''
                for paper in papers_bar:
                    if not is_start:
                        if 'h2' == paper.name:  # find 'content'
                            if 'Contents' == paper.text:
                                is_start = True
                    else:
                        if 'h3' == paper.name: # group
                            this_group = slugify(paper.text)
                        elif 'p' == paper.name:  # paper
                            all_as = paper.find_all('a')
                            if len(all_as) >= 2:  # paper pdf and abstract
                                paper_index += 1
                                title = slugify(paper.text.split('\n')[0])
                                papers_bar.set_description(f'downloading paper {paper_index}: {title}')
                                is_get_link = False
                                for a in all_as:
                                    if 'PDF' == a.text:
                                        link = 'https://www.ijcai.org' + a.get('href')
                                        is_get_link = True
                                        break
                                if is_get_link:
                                    paper_dict = {'title': title,
                                                  'link': link,
                                                  'group': this_group}
                                else:
                                    paper_dict = {'title': title,
                                                  'link': 'error',
                                                  'group': this_group}
                                    print(f'get link for {title}_{year} failed!')
                                    error_log.apend(title, 'no link')
                                writer.writerow(paper_dict)
            elif year in [2013, 2011, 2009, 2007]:  # p group
                div_content = soup.find('div', {'id': 'content'})
                papers_bar = tqdm(div_content.find_all(['h2', 'p', 'h3', 'h4']))
                # papers_bar = div_content.find_all(['h2', 'p', 'h3', 'h4'])
                is_start = False
                this_group = ''
                this_group_v3 = ''
                this_group_v4 = ''
                for paper in papers_bar:
                    if not is_start:
                        if 'h2' == paper.name:  # find 'content'
                            if 'Contents' == paper.text or 'IJCAI-09 Contents' == paper.text or \
                                    'IJCAI-07 Contents' == paper.text:
                                is_start = True
                    else:
                        if 'h3' == paper.name: # group
                            this_group_v3 = slugify(paper.text)
                            this_group = this_group_v3
                        elif 'h4' == paper.name: # group
                            this_group_v4 = slugify(paper.text)
                            this_group = this_group_v3 + '--' + this_group_v4
                        elif 'p' == paper.name:  # paper
                            try:
                                all_as = paper.find_all('a')
                            except:
                                continue
                            if len(all_as) >= 1:  # paper
                                paper_index += 1
                                is_get_link = False
                                for a in all_as:
                                    if 'abstract' != slugify(a.text.strip()):
                                        title = slugify(a.text)
                                        link = a.get('href')
                                        is_get_link = True
                                        papers_bar.set_description(f'downloading paper {paper_index}: {title}')
                                        break
                                if is_get_link:
                                    paper_dict = {'title': title,
                                                  'link': link,
                                                  'group': this_group}
                                else:
                                    paper_dict = {'title': title,
                                                  'link': 'error',
                                                  'group': this_group}
                                    print(f'get link for {title}_{year} failed!')
                                    error_log.apend(title, 'no link')
                                # papers_bar.set_description(f'downloading paper {paper_index}: {title}')
                                writer.writerow(paper_dict)
            elif year in [2005]:
                div_content = soup.find('div', {'id': 'content'})
                papers_bar = tqdm(div_content.find_all(['p']))
                this_group = ''
                for paper in papers_bar:
                    try:
                        paper_class = paper.get('class')[0]
                    except:
                        continue
                    if 'docsection' == paper_class:  # group
                        this_group = slugify(paper.text)
                    elif 'doctitle' == paper_class:  # paper
                        paper_index += 1
                        title = slugify(paper.a.text)
                        link = paper.a.get('href')
                        papers_bar.set_description(f'downloading paper {paper_index}: {title}')
                        paper_dict = {'title': title,
                                      'link': link,
                                      'group': this_group}
                        writer.writerow(paper_dict)
            elif year in [2003]:
                div_content = soup.find('div', {'id': 'content'})
                papers_bar = tqdm(div_content.find_all(['p']))
                this_group = ''
                for paper in papers_bar:
                    try:
                        this_group = slugify(paper.b.text)
                    except:
                        pass
                    try:
                        title = slugify(paper.a.text)
                        link = paper.a.get('href')
                        paper_index += 1
                        papers_bar.set_description(f'downloading paper {paper_index}: {title}')
                        paper_dict = {'title': title,
                                      'link': link,
                                      'group': this_group}
                        writer.writerow(paper_dict)
                    except:
                        continue
            elif year in [2001]:
                div_content = soup.find('div', {'id': 'content'})
                papers_bar = tqdm(div_content.find_all(['p']))
                this_group = ''
                for paper in papers_bar:
                    try:
                        title = slugify(paper.a.text)
                        link = paper.a.get('href')
                        paper_index += 1
                        papers_bar.set_description(f'downloading paper {paper_index}: {title}')
                        paper_dict = {'title': title,
                                      'link': link,
                                      'group': this_group}
                        writer.writerow(paper_dict)
                    except:
                        continue
            elif year in [1999, 1997, 1995, 1993, 1991, 1989, 1987, 1981, 1979, 1977, 1969]:  # goup in capital in p.b.text
                div_content = soup.find('div', {'id': 'content'})
                papers_bar = tqdm(div_content.find_all(['p']))
                this_group = ''
                for paper in papers_bar:
                    try:
                        if paper.b.text.isupper():
                            # print(paper.b.text)
                            this_group = slugify(paper.b.text)
                    except:
                        pass
                    try:
                        for a in paper.find_all('a'):
                            title = slugify(a.text.strip())
                            link = a.get('href')
                            if link[-3:] == 'pdf' and '' != title:
                                paper_index += 1
                                papers_bar.set_description(f'downloading paper {paper_index}: {title}')
                                paper_dict = {'title': title,
                                              'link': link,
                                              'group': this_group}
                                writer.writerow(paper_dict)
                                break
                            else:
                                continue

                    except:
                        continue
            elif year in [1985, 1975, 1971]:  # no group, paper in 'p'
                div_content = soup.find('div', {'id': 'content'})
                papers_bar = tqdm(div_content.find_all(['p']))
                this_group = ''
                for paper in papers_bar:
                    try:
                        for a in paper.find_all('a'):
                            title = slugify(a.text.strip())
                            link = a.get('href')
                            if link[-3:] == 'pdf' and '' != title:
                                paper_index += 1
                                papers_bar.set_description(f'downloading paper {paper_index}: {title}')
                                paper_dict = {'title': title,
                                              'link': link,
                                              'group': this_group}
                                writer.writerow(paper_dict)
                                break
                            else:
                                continue

                    except:
                        continue
            elif year in [1983]:  # goup in capital p.text
                div_content = soup.find('div', {'id': 'content'})
                papers_bar = tqdm(div_content.find_all(['p']))
                this_group = ''
                for paper in papers_bar:
                    try:
                        if paper.text.isupper():
                            this_group = slugify(paper.text)
                    except:
                        pass
                    try:
                        for a in paper.find_all('a'):
                            title = slugify(a.text.strip())
                            link = a.get('href')
                            if link[-3:] == 'pdf' and '' != title:
                                paper_index += 1
                                papers_bar.set_description(f'downloading paper {paper_index}: {title}')
                                paper_dict = {'title': title,
                                              'link': link,
                                              'group': this_group}
                                writer.writerow(paper_dict)
                                break
                            else:
                                continue

                    except:
                        continue
            elif year in [1973]:  # goup in p.b
                div_content = soup.find('div', {'id': 'content'})
                papers_bar = tqdm(div_content.find_all(['p']))
                this_group = ''
                for paper in papers_bar:
                    try:
                        if '' != paper.b.text.strip():
                            this_group = slugify(paper.b.text.strip())
                    except:
                        pass
                    try:
                        for a in paper.find_all('a'):
                            title = slugify(a.text.strip())
                            link = a.get('href')
                            if link[-3:] == 'pdf' and '' != title:
                                paper_index += 1
                                papers_bar.set_description(f'downloading paper {paper_index}: {title}')
                                paper_dict = {'title': title,
                                              'link': link,
                                              'group': this_group}
                                writer.writerow(paper_dict)
                                break
                            else:
                                continue

                    except:
                        continue
        #  write error log
        print('write error log')
        with open('download_err_log.txt', 'w') as f:
            for log in tqdm(error_log):
                for e in log:
                    if e is not None:
                        f.write(e)
                    else:
                        f.write('None')
                    f.write('\n')

                f.write('\n')


def download_from_csv(year, save_dir, time_step_in_seconds=5):
    """
    download all IJCAI paper given year
    :param year: int, IJCAI year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :return: True
    """
    # use IDM to download everything
    idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'''  # should replace by the local IDM path
    basic_command = [idm_path, '/d', 'xxxx', '/p', os.getcwd(), '/f', 'xxxx', '/n']

    error_log = []
    postfix = f'IJCAI_{year}'
    with open(f'IJCAI_{year}.csv', newline='') as csvfile:
        myreader = csv.DictReader(csvfile, delimiter=',')
        pbar = tqdm(myreader)
        i = 0
        for this_paper in pbar:
            i += 1
            # get title
            print('\n')
            title = slugify(this_paper['title'])
            # print('Downloading paper {}: {}'.format(i, title))

            if '' != this_paper['group']:
                this_paper_main_path = os.path.join(save_dir, slugify(this_paper['group']), f'{title}_{postfix}.pdf')
            else:
                this_paper_main_path = os.path.join(save_dir, f'{title}_{postfix}.pdf')
            if os.path.exists(this_paper_main_path):
                continue
            if 'error' == this_paper['link']:
                error_log.append((title, 'no link'))
            elif '' != this_paper['link']:
                if '' != this_paper['group']:
                    os.makedirs(os.path.join(save_dir, slugify(this_paper['group'])), exist_ok=True)
                try:
                    # download paper with IDM
                    if not os.path.exists(this_paper_main_path):
                        # print('title')
                        pbar.set_description(f'Downloading paper {i}')
                        basic_command[2] = this_paper['link']
                        basic_command[6] = this_paper_main_path
                        p = subprocess.Popen(' '.join(basic_command))
                        p.wait()
                        time.sleep(time_step_in_seconds)
                        # while True:
                        #     if os.path.exists(this_paper_main_path):
                        #         break
                except Exception as e:
                    # error_flag = True
                    print('Error: ' + title + ' - ' + str(e))
                    error_log.append((title, this_paper['link'], 'paper download error', str(e)))

        # 2. write error log
        print('write error log')
        with open('download_err_log.txt', 'w') as f:
            for log in tqdm(error_log):
                for e in log:
                    if e is not None:
                        f.write(e)
                    else:
                        f.write('None')
                    f.write('\n')

                f.write('\n')


if __name__ == '__main__':
    # for year in  range(1993, 1968, -2):
    #     print(year)
    #     # save_csv(year)
    #     # time.sleep(2)
    #     download_from_csv(year, save_dir=f'..\\IJCAI_{year}', time_step_in_seconds=1)
    year = 1983
    # save_csv(year)
    download_from_csv(year, save_dir=f'..\\IJCAI_{year}', time_step_in_seconds=1)
    pass