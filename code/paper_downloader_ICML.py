"""paper_downloader_ICML.py"""

import urllib
from bs4 import BeautifulSoup
import pickle
import os
from tqdm import tqdm
from slugify import slugify
import sys
root_folder = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
from lib.downloader import Downloader
import lib.pmlr as pmlr
from lib.supplement_porcess import merge_main_supplement
from lib.openreview import download_icml_papers_given_url_and_group_id
from lib.my_request import urlopen_with_retry


def download_paper(year, save_dir, is_download_supplement=True,
                   time_step_in_seconds=5, downloader='IDM', source='pmlr',
                   proxy_ip_port=None):
    """
    download all ICML paper and supplement files given year, restore in
        save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, ICML year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental
        material
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder', default to 'IDM'
    :param source: str, source website, 'pmlr' or 'openreview'
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Default: None.
    :type proxy_ip_port: str | None
    :return: True
    """
    assert source in ['pmlr', 'openreview'], \
        f'only support source pmlr or openreview, but get {source}'
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    downloader = Downloader(downloader=downloader, proxy_ip_port=proxy_ip_port)
    ICML_year_dict = {
        2024: 235,
        2023: 202,
        2022: 162,
        2021: 139,
        2020: 119,
        2019: 97,
        2018: 80,
        2017: 70,
        2016: 48,
        2015: 37,
        2014: 32,
        2013: 28
    }
    if source == 'openreview':
        init_url = f'https://openreview.net/group?id=ICML.cc/{year}/Conference'
    else:  # pmlr
        if year >= 2013:
            init_url = f'http://proceedings.mlr.press/v{ICML_year_dict[year]}/'
        elif year == 2012:
            init_url = 'https://icml.cc/2012/papers.1.html'
        elif year == 2011:
            init_url = 'http://www.icml-2011.org/papers.php'
        elif 2009 == year:
            init_url = 'https://icml.cc/Conferences/2009/abstracts.html'
        elif 2008 == year:
            init_url = 'http://www.machinelearning.org/archive/icml2008/' \
                       'abstracts.shtml'
        elif 2007 == year:
            init_url = 'https://icml.cc/Conferences/2007/paperlist.html'
        elif year in [2006, 2004, 2005]:
            init_url = f'https://icml.cc/Conferences/{year}/proceedings.html'
        elif 2003 == year:
            init_url = 'https://aaai.org/Library/ICML/icml03contents.php'
        else:
            raise ValueError('''the given year's url is unknown !''')

    postfix = f'ICML_{year}'
    if source == 'openreview':  # download from openreview website:
        # oral paper
        group_id = 'oral'
        save_dir_oral = os.path.join(save_dir, group_id)
        os.makedirs(save_dir_oral, exist_ok=True)
        download_icml_papers_given_url_and_group_id(
            save_dir=save_dir_oral,
            year=year,
            base_url=init_url,
            group_id=group_id,
            start_page=1,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader.downloader,
            proxy_ip_port=proxy_ip_port
        )
        # poster paper
        group_id = 'poster'
        save_dir_poster = os.path.join(save_dir, group_id)
        os.makedirs(save_dir_poster, exist_ok=True)
        download_icml_papers_given_url_and_group_id(
            save_dir=os.path.join(save_dir, 'poster'),
            year=year,
            base_url=init_url,
            group_id=group_id,
            start_page=1,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader.downloader,
            proxy_ip_port=proxy_ip_port
        )
        # spotlight paper
        group_id = 'spotlight'
        save_dir_poster = os.path.join(save_dir, group_id)
        os.makedirs(save_dir_poster, exist_ok=True)
        try:
            download_icml_papers_given_url_and_group_id(
                save_dir=os.path.join(save_dir, 'spotlight'),
                year=year,
                base_url=init_url,
                group_id=group_id,
                start_page=1,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader.downloader,
                proxy_ip_port=proxy_ip_port
            )
        except ValueError as e:  # no spotlight paper
            print(f"WARNING: {str(e)}")
        return

    dat_file_pathname = os.path.join(
        project_root_folder, 'urls', f'init_url_icml_{year}.dat')
    if os.path.exists(dat_file_pathname):
        with open(dat_file_pathname, 'rb') as f:
            content = pickle.load(f)
    else:
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
                'Gecko/20100101 Firefox/23.0'}
        content = urlopen_with_retry(url=init_url, headers=headers)
        # content = open(f'..\\ICML_{year}.html', 'rb').read()
        with open(dat_file_pathname, 'wb') as f:
            pickle.dump(content, f)
    # soup = BeautifulSoup(content, 'html.parser')
    soup = BeautifulSoup(content, 'html5lib')
    # soup = BeautifulSoup(open(r'..\ICML_2011.html', 'rb'), 'html.parser')
    error_log = []
    if year >= 2013:
        if year in ICML_year_dict.keys():
            volume = f'v{ICML_year_dict[year]}'
        else:
            raise ValueError('''the given year's url is unknown !''')

        pmlr.download_paper_given_volume(
            volume=volume,
            save_dir=save_dir,
            postfix=postfix,
            is_download_supplement=is_download_supplement,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader.downloader
        )
    elif 2012 == year:  # 2012
        # base_url = f'https://icml.cc/{year}/'
        paper_list_bar = tqdm(soup.find_all('div', {'class': 'paper'}))
        paper_index = 0
        for paper in paper_list_bar:
            paper_index += 1
            title = ''
            title = slugify(paper.find('h2').text)
            link = None
            for a in paper.find_all('a'):
                if 'ICML version (pdf)' == a.text:
                    link = urllib.parse.urljoin(init_url, a.get('href'))
                    break
            if link is not None:
                this_paper_main_path = os.path.join(
                    save_dir, f'{title}_{postfix}.pdf'.replace(' ', '_'))
                paper_list_bar.set_description(
                    f'find paper {paper_index}:{title}')
                if not os.path.exists(this_paper_main_path) :
                    paper_list_bar.set_description(
                        f'downloading paper {paper_index}:{title}')
                    downloader.download(
                        urls=link,
                        save_path=this_paper_main_path,
                        time_sleep_in_seconds=time_step_in_seconds
                    )
            else:
                error_log.append((title, 'no main link error'))
    elif 2011 == year:
        paper_list_bar = tqdm(soup.find_all('a'))
        paper_index = 0
        for paper in paper_list_bar:
            h3 = paper.find('h3')
            if h3 is not None:
                title = slugify(h3.text)
                paper_index += 1
            if 'download' == slugify(paper.text.strip()):
                link = paper.get('href')
                link = urllib.parse.urljoin(init_url, link)
                if link is not None:
                    this_paper_main_path = os.path.join(
                        save_dir, f'{title}_{postfix}.pdf'.replace(' ', '_'))
                    paper_list_bar.set_description(
                        f'find paper {paper_index}:{title}')
                    if not os.path.exists(this_paper_main_path) :
                        paper_list_bar.set_description(
                            f'downloading paper {paper_index}:{title}')
                        downloader.download(
                            urls=link,
                            save_path=this_paper_main_path,
                            time_sleep_in_seconds=time_step_in_seconds
                        )
                else:
                    error_log.append((title, 'no main link error'))
    elif year in [2009, 2008]:
        if 2009 == year:
            paper_list_bar = tqdm(
                soup.find('div', {'id': 'right_column'}).find_all(['h3','a']))
        elif 2008 == year:
            paper_list_bar = tqdm(
                soup.find('div', {'class': 'content'}).find_all(['h3','a']))
        paper_index = 0
        title = None
        for paper in paper_list_bar:
            if 'h3' == paper.name:
                title = slugify(paper.text)
                paper_index += 1
            elif 'full-paper' == slugify(paper.text.strip()):  # a
                link = paper.get('href')
                if link is not None and title is not None:
                    link = urllib.parse.urljoin(init_url, link)
                    this_paper_main_path = os.path.join(
                        save_dir, f'{title}_{postfix}.pdf')
                    paper_list_bar.set_description(
                        f'find paper {paper_index}:{title}')
                    if not os.path.exists(this_paper_main_path):
                        paper_list_bar.set_description(
                            f'downloading paper {paper_index}:{title}')
                        downloader.download(
                            urls=link,
                            save_path=this_paper_main_path,
                            time_sleep_in_seconds=time_step_in_seconds
                        )
                    title = None
                else:
                    error_log.append((title, 'no main link error'))
    elif year in [2006, 2005]:
        paper_list_bar = tqdm(soup.find_all('a'))
        paper_index = 0
        for paper in paper_list_bar:
            title = slugify(paper.text.strip())
            link = paper.get('href')
            paper_index += 1
            if link is not None and title is not None and \
                    ('pdf' == link[-3:] or 'ps' == link[-2:]):
                link = urllib.parse.urljoin(init_url, link)
                this_paper_main_path = os.path.join(
                    save_dir, f'{title}_{postfix}.pdf'.replace(' ', '_'))
                paper_list_bar.set_description(
                    f'find paper {paper_index}:{title}')
                if not os.path.exists(this_paper_main_path):
                    paper_list_bar.set_description(
                        f'downloading paper {paper_index}:{title}')
                    downloader.download(
                        urls=link,
                        save_path=this_paper_main_path,
                        time_sleep_in_seconds=time_step_in_seconds
                    )
    elif 2004 == year:
        paper_index = 0
        paper_list_bar = tqdm(
            soup.find('table', {'class': 'proceedings'}).find_all('tr'))
        title = None
        for paper in paper_list_bar:
            tr_class = None
            try:
                tr_class = paper.get('class')[0]
            except:
                pass
            if 'proc_2004_title' == tr_class:  # title
                title = slugify(paper.text.strip())
                paper_index += 1
            else:
                for a in paper.find_all('a'):
                    if '[Paper]' == a.text:
                        link = a.get('href')
                        if link is not None and title is not None:
                            link = urllib.parse.urljoin(init_url, link)
                            this_paper_main_path = os.path.join(
                                save_dir,
                                f'{title}_{postfix}.pdf'.replace(' ', '_'))
                            paper_list_bar.set_description(
                                f'find paper {paper_index}:{title}')
                            if not os.path.exists(this_paper_main_path):
                                paper_list_bar.set_description(
                                    f'downloading paper {paper_index}:{title}')
                                downloader.download(
                                    urls=link,
                                    save_path=this_paper_main_path,
                                    time_sleep_in_seconds=time_step_in_seconds
                                )
                        break
    elif 2003 == year:
        paper_index = 0
        paper_list_bar = tqdm(
            soup.find('div', {'id': 'content'}).find_all(
                'p', {'class': 'left'}))
        for paper in paper_list_bar:
            abs_link = None
            title = None
            link = None
            for a in paper.find_all('a'):
                abs_link = urllib.parse.urljoin(init_url, a.get('href'))
                if abs_link is not None:
                    title = slugify(a.text.strip())
                    break
            if title is not None:
                paper_index += 1
                this_paper_main_path = os.path.join(
                    save_dir, f'{title}_{postfix}.pdf'.replace(' ', '_'))
                paper_list_bar.set_description(
                    f'find paper {paper_index}:{title}')
                if not os.path.exists(this_paper_main_path):
                    if abs_link is not None:
                        headers = {'User-Agent':
                                       'Mozilla/5.0 (Windows NT 6.1; WOW64; '
                                       'rv:23.0) Gecko/20100101 Firefox/23.0'}
                        abs_content = urlopen_with_retry(
                            url=abs_link, headers=headers,
                            raise_error_if_failed=False)
                        if abs_content is None:
                            print('error'+title)
                            error_log.append(
                                (title, abs_link, 'download error'))
                            continue
                        abs_soup = BeautifulSoup(abs_content, 'html5lib')
                        for a in abs_soup.find_all('a'):
                            try:
                                if 'pdf' == a.get('href')[-3:]:
                                    link = urllib.parse.urljoin(
                                        abs_link, a.get('href'))
                                    if link is not None:
                                        paper_list_bar.set_description(
                                            f'downloading paper {paper_index}:'
                                            f'{title}')
                                        downloader.download(
                                            urls=link,
                                            save_path=this_paper_main_path,
                                            time_sleep_in_seconds=time_step_in_seconds
                                        )
                                    break
                            except:
                                pass

    # write error log
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


def rename_downloaded_paper(year, source_path):
    """
    rename the downloaded ICML paper to {title}_ICML_2010.pdf and save to
    source_path
    :param year: int, year
    :param source_path: str, whose structure should be
        source_path/papers/pdf files (2010)
                   /index.html       (2010)
        source_path/icml2007_proc.html (2007)
   :return:
    """
    if not os.path.exists(source_path):
        raise ValueError(f'can not find {source_path}')
    postfix = f'ICML_{year}'
    if 2010 == year:
        soup = BeautifulSoup(
            open(os.path.join(source_path, 'index.html'), 'rb'), 'html5lib')
        paper_list_bar = tqdm(soup.find_all('span', {'class': 'boxpopup3'}))

        for paper in paper_list_bar:
            a = paper.find('a')
            title = slugify(a.text)
            ori_name = os.path.join(
                source_path, 'papers', a.get('href').split('/')[-1])
            os.rename(ori_name, os.path.join(
                source_path, f'{title}_{postfix}.pdf'))
            paper_list_bar.set_description(f'processing {title}')
    elif 2007 == year:
        soup = BeautifulSoup(open(os.path.join(
            source_path, 'icml2007_proc.html'), 'rb'), 'html5lib')
        paper_list_bar = tqdm(soup.find_all('td', {'colspan': '2'}))
        for paper in paper_list_bar:
            all_as = paper.find_all('a')
            if len(all_as) <= 1:
                title = slugify(paper.text.strip())
            else:
                for a in all_as:
                    if '[Paper]' == a.text:
                        sub_path = a.get('href')
                        os.rename(os.path.join(source_path, sub_path),
                                  os.path.join(
                                      source_path, f'{title}_{postfix}.pdf'))
                        paper_list_bar.set_description_str(
                            (f'processing {title}'))
                        break


if __name__ == '__main__':
    year = 2025
    download_paper(
        year,
        rf'E:\ICML_{year}',
        is_download_supplement=True,
        time_step_in_seconds=10,
        downloader='IDM',
        source='openreview'
    ) 
    # merge_main_supplement(main_path=f'..\\ICML_{year}\\main_paper',
    #                       supplement_path=f'..\\ICML_{year}\\supplement',
    #                       save_path=f'..\\ICML_{year}',
    #                       is_delete_ori_files=False)
    # rename_downloaded_paper(year, f'..\\ICML_{year}')
    pass
