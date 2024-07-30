"""paper_downloader_IJCAI.py"""

import urllib
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
    write IJCAI papers' urls in one csv file
    :param year: int, IJCAI year, such 2019
    :return: peper_index: int, the total number of papers
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_file_pathname = os.path.join(
        project_root_folder, 'csv', f'IJCAI_{year}.csv'
    )
    with open(csv_file_pathname, 'w', newline='') as csvfile:
        fieldnames = ['title', 'main link', 'group']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        if year >= 2003:
            init_urls = [f'https://www.ijcai.org/proceedings/{year}/']
        elif year >= 1977:
            init_urls = [f'https://www.ijcai.org/Proceedings/{year}-1/',
                         f'https://www.ijcai.org/Proceedings/{year}-2/']
        elif year >= 1969:
            init_urls = [f'https://www.ijcai.org/Proceedings/{year}/']
        else:
            raise ValueError('invalid year!')
        error_log = []
        user_agents = [
            'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) '
            'Gecko/20071127 Firefox/2.0.0.11',

            'Opera/9.25 (Windows NT 5.1; U; en)',

            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; '
            '.NET CLR 1.1.4322; .NET CLR 2.0.50727)',

            'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) '
            'KHTML/3.5.5 (like Gecko) (Kubuntu)',

            'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) '
            'Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',

            'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',

            "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 "
            "(KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 "
            "Chrome/16.0.912.77 Safari/535.7",

            "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) "
            "Gecko/20100101 Firefox/10.0 ",

            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/105.0.0.0 Safari/537.36'

        ]
        headers = {
            'User-Agent': user_agents[-1],
            'Host': 'www.ijcai.org',
            'Referer': "https://www.ijcai.org",
            'GET': init_urls[0]
        }
        if len(init_urls) == 1:
            data_file_pathname = os.path.join(
                project_root_folder, 'urls', f'init_url_IJCAI_{year}.dat'
            )
            if os.path.exists(data_file_pathname):
                with open(data_file_pathname, 'rb') as f:
                    content = pickle.load(f)
            else:
                content = urlopen_with_retry(url=init_urls[0], headers=headers)
                with open(data_file_pathname, 'wb') as f:
                    pickle.dump(content, f)
            contents = [content]
        else:
            contents = []
            data_file_pathname = os.path.join(
                project_root_folder, 'urls', f'init_url_IJCAI_0_{year}.dat'
            )
            if os.path.exists(data_file_pathname):
                with open(data_file_pathname, 'rb') as f:
                    content = pickle.load(f)
            else:
                content = urlopen_with_retry(url=init_urls[0], headers=headers)
                with open(data_file_pathname, 'wb') as f:
                    pickle.dump(content, f)
            contents.append(content)
            data_file_pathname = os.path.join(
                project_root_folder, 'urls', f'init_url_IJCAI_1_{year}.dat'
            )
            if os.path.exists(data_file_pathname):
                with open(data_file_pathname, 'rb') as f:
                    content = pickle.load(f)
            else:
                content = urlopen_with_retry(url=init_urls[1], headers=headers)
                with open(data_file_pathname, 'wb') as f:
                    pickle.dump(content, f)
            contents.append(content)
        paper_index = 0
        for content in contents:
            soup = BeautifulSoup(content, 'html5lib')
            if year >= 2017:
                pbar = tqdm(soup.find_all('div', {'class': 'section_title'}))
                for section in pbar:
                    this_group = slugify(section.text)
                    papers = section.parent.find_all(
                        'div', {'class': ['paper_wrapper', 'subsection_title']})
                    sub_group = ''
                    for paper in papers:
                        if 'subsection_title' == paper.get('class')[0]:
                            sub_group = slugify(paper.text)
                            continue
                        paper_index += 1
                        is_get_link = False
                        title = slugify(
                            paper.find('div', {'class': 'title'}).text)
                        pbar.set_description(
                            f'downloading paper {paper_index}: {title}')
                        for a in paper.find(
                                'div', {'class': 'details'}).find_all('a'):
                            if 'PDF' == a.text:
                                link = urllib.parse.urljoin(
                                    init_urls[0], a.get('href'))
                                is_get_link = True
                                break
                        if is_get_link:
                            paper_dict = {'title': title,
                                          'main link': link,
                                          'group': this_group + '--' +
                                                   sub_group if
                                          sub_group != '' else this_group}
                        else:
                            paper_dict = {'title': title,
                                          'main link': 'error',
                                          'group': this_group + '--' +
                                                   sub_group if
                                          sub_group != '' else this_group}
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
                        papers_bar.set_description(
                            f'downloading paper {paper_index}: {title}')
                        is_get_link = False
                        for a in all_as:
                            if 'PDF' == a.text:
                                link = 'https://www.ijcai.org' + a.get('href')
                                is_get_link = True
                                break
                        if is_get_link:
                            paper_dict = {'title': title,
                                          'main link': link,
                                          'group': ''}
                        else:
                            paper_dict = {'title': title,
                                          'main link': 'error',
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
                                papers_bar.set_description(
                                    f'downloading paper {paper_index}: {title}')
                                is_get_link = False
                                for a in all_as:
                                    if 'PDF' == a.text:
                                        link = 'https://www.ijcai.org' + \
                                               a.get('href')
                                        is_get_link = True
                                        break
                                if is_get_link:
                                    paper_dict = {'title': title,
                                                  'main link': link,
                                                  'group': this_group}
                                else:
                                    paper_dict = {'title': title,
                                                  'main link': 'error',
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
                            if 'Contents' == paper.text or \
                                    'IJCAI-09 Contents' == paper.text or \
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
                                        papers_bar.set_description(
                                            f'downloading paper {paper_index}: '
                                            f'{title}')
                                        break
                                if is_get_link:
                                    paper_dict = {'title': title,
                                                  'main link': link,
                                                  'group': this_group}
                                else:
                                    paper_dict = {'title': title,
                                                  'main link': 'error',
                                                  'group': this_group}
                                    print(f'get link for {title}_{year} failed!')
                                    error_log.append((title, 'no link'))
                                # papers_bar.set_description(f'downloading
                                # paper {paper_index}: {title}')
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
                        papers_bar.set_description(
                            f'downloading paper {paper_index}: {title}')
                        paper_dict = {'title': title,
                                      'main link': link,
                                      'group': this_group}
                        writer.writerow(paper_dict)
            elif year in [2003]:
                div_content = soup.find('div', {'id': 'content'})
                papers_bar = tqdm(div_content.find_all(['p']))
                this_group = ''
                base_url = 'https://www.ijcai.org'
                for paper in papers_bar:
                    try:
                        this_group = slugify(paper.b.text)
                    except:
                        pass
                    try:
                        title = slugify(paper.a.text)
                        link = base_url + paper.a.get('href')
                        paper_index += 1
                        papers_bar.set_description(
                            f'downloading paper {paper_index}: {title}')
                        paper_dict = {'title': title,
                                      'main link': link,
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
                        papers_bar.set_description(
                            f'downloading paper {paper_index}: {title}')
                        paper_dict = {'title': title,
                                      'main link': link,
                                      'group': this_group}
                        writer.writerow(paper_dict)
                    except:
                        continue
            elif year in [1999, 1997, 1995, 1993, 1991, 1989, 1987, 1981, 1979,
                          1977, 1969]:  # goup in capital in p.b.text
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
                                papers_bar.set_description(
                                    f'downloading paper {paper_index}: {title}')
                                paper_dict = {'title': title,
                                              'main link': link,
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
                                papers_bar.set_description(
                                    f'downloading paper {paper_index}: {title}')
                                paper_dict = {'title': title,
                                              'main link': link,
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
                                papers_bar.set_description(
                                    f'downloading paper {paper_index}: {title}')
                                paper_dict = {'title': title,
                                              'main link': link,
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
                                papers_bar.set_description(
                                    f'downloading paper {paper_index}: {title}')
                                paper_dict = {'title': title,
                                              'main link': link,
                                              'group': this_group}
                                writer.writerow(paper_dict)
                                break
                            else:
                                continue

                    except:
                        continue
        #  write error log
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

    return paper_index if paper_index is not None else None


def download_from_csv(
        year, save_dir, time_step_in_seconds=5, total_paper_number=None, downloader='IDM'):
    """
    download all IJCAI paper given year
    :param year: int, IJCAI year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :param total_paper_number: int, the total number of papers that is going to download
    :param downloader: str, the downloader to download, could be 'IDM' or 'Thunder', default to 'IDM'
    :return: True
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    postfix = f'IJCAI_{year}'
    csv_filename = f'IJCAI_{year}.csv'
    csv_filename = os.path.join(project_root_folder, 'csv', csv_filename)
    csv_process.download_from_csv(
        postfix=postfix,
        save_dir=save_dir,
        csv_file_path=csv_filename,
        is_download_supplement=False,
        time_step_in_seconds=time_step_in_seconds,
        total_paper_number=total_paper_number,
        downloader=downloader
    )


if __name__ == '__main__':
    # for year in  range(1993, 1968, -2):
    #     print(year)
    #     # save_csv(year)
    #     # time.sleep(2)
    #     download_from_csv(year, save_dir=f'..\\IJCAI_{year}',
    #     time_step_in_seconds=1)
    year = 2024
    # total_paper_number = 723
    total_paper_number = save_csv(year)
    download_from_csv(
        year,
        save_dir=fr'E:\IJCAI_{year}',
        time_step_in_seconds=5,
        total_paper_number=total_paper_number,
        downloader=None)

    pass
