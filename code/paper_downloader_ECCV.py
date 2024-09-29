"""paper_downloader_ECCV.py"""

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
from lib.supplement_porcess import move_main_and_supplement_2_one_directory
import lib.springer as springer
from lib import csv_process
from lib.downloader import Downloader
from lib.my_request import urlopen_with_retry


def save_csv(year):
    """
    write ECCV papers' and supplemental material's urls in one csv file
    :param year: int
    :return: True
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_file_pathname = os.path.join(
        project_root_folder, 'csv', f'ECCV_{year}.csv')
    with open(csv_file_pathname, 'w', newline='') as csvfile:
        fieldnames = ['title', 'main link', 'supplemental link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
                'Gecko/20100101 Firefox/23.0'}
        dat_file_pathname = os.path.join(
            project_root_folder, 'urls', f'init_url_ECCV_{year}.dat')
        if year >= 2018:
            init_url = f'https://www.ecva.net/papers.php'
            if os.path.exists(dat_file_pathname):
                with open(dat_file_pathname, 'rb') as f:
                    content = pickle.load(f)
            else:
                content = urlopen_with_retry(url=init_url, headers=headers)
                with open(dat_file_pathname, 'wb') as f:
                    pickle.dump(content, f)
            soup = BeautifulSoup(content, 'html5lib')
            paper_list_bar = tqdm(soup.find_all(['dt', 'dd']))
            paper_index = 0
            paper_dict = {'title': '',
                          'main link': '',
                          'supplemental link': ''}
            for paper in paper_list_bar:
                is_new_paper = False

                # get title
                try:
                    if 'dt' == paper.name and \
                            'ptitle' == paper.get('class')[0] and \
                            year == int(paper.a.get('href').split('_')[1][:4]):  # title:
                        # this_year = int(paper.a.get('href').split('_')[1][:4])
                        title = slugify(paper.text.strip())
                        paper_dict['title'] = title
                        paper_index += 1
                        paper_list_bar.set_description_str(
                            f'Downloading paper {paper_index}: {title}')
                    elif '' != paper_dict['title'] and 'dd' == paper.name:
                        all_as = paper.find_all('a')
                        for a in all_as:
                            if 'pdf' == slugify(a.text.strip()):
                                main_link = urllib.parse.urljoin(init_url,
                                                                 a.get('href'))
                                paper_dict['main link'] = main_link
                                is_new_paper = True
                            elif 'supp' in slugify(a.text.strip()):
                                supp_link = urllib.parse.urljoin(init_url,
                                                                 a.get('href'))
                                paper_dict['supplemental link'] = supp_link
                                break
                except:
                    pass
                if is_new_paper:
                    writer.writerow(paper_dict)
                    paper_dict = {'title': '',
                                  'main link': '',
                                  'supplemental link': ''}
        else:
            init_url = f'http://www.eccv{year}.org/main-conference/'
            if os.path.exists(dat_file_pathname):
                with open(dat_file_pathname, 'rb') as f:
                    content = pickle.load(f)
            else:
                content = urlopen_with_retry(url=init_url, headers=headers)
                with open(dat_file_pathname, 'wb') as f:
                    pickle.dump(content, f)
            soup = BeautifulSoup(content, 'html5lib')
            paper_list_bar = tqdm(
                soup.find('div', {'class': 'entry-content'}).find_all(['p']))
            paper_index = 0
            paper_dict = {'title': '',
                          'main link': '',
                          'supplemental link': ''}
            for paper in paper_list_bar:
                try:
                    if len(paper.find_all(['strong'])) and len(
                            paper.find_all(['a'])) and len(
                            paper.find_all(['img'])):
                        paper_index += 1
                        title = slugify(paper.find('strong').text)
                        paper_dict['title'] = title
                        paper_list_bar.set_description_str(
                            f'Downloading paper {paper_index}: {title}')
                        main_link = paper.find('a').get('href')
                        paper_dict['main link'] = main_link
                        writer.writerow(paper_dict)
                        paper_dict = {'title': '',
                                      'main link': '',
                                      'supplemental link': ''}
                except Exception as e:
                    print(f'ERROR: {str(e)}')
    return paper_index


def download_from_csv(
        year, save_dir, is_download_supplement=True, time_step_in_seconds=5,
        total_paper_number=None,
        is_workshops=False, downloader='IDM'):
    """
    download all ECCV paper and supplement files given year, restore in
    save_dir/main_paper and save_dir/supplement respectively
    :param year: int, ECCV year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental
        material
    :param time_step_in_seconds: int, the interval time between two downlaod
        request in seconds
    :param total_paper_number: int, the total number of papers that is going
        to download
    :param is_workshops: bool, is to download workshops from csv file.
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder', default to 'IDM'
    :return: True
    """
    postfix = f'ECCV_{year}'
    if is_workshops:
        postfix = f'ECCV_WS_{year}'
    csv_file_name = f'ECCV_{year}.csv' if not is_workshops else \
        f'ECCV_WS_{year}.csv'
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_file_name = os.path.join(project_root_folder, 'csv', csv_file_name)
    csv_process.download_from_csv(
        postfix=postfix,
        save_dir=save_dir,
        csv_file_path=csv_file_name,
        is_download_supplement=is_download_supplement,
        time_step_in_seconds=time_step_in_seconds,
        total_paper_number=total_paper_number,
        downloader=downloader
    )


def download_from_springer(
        year, save_dir, is_workshops=False, time_sleep_in_seconds=5,
        downloader='IDM'):
    os.makedirs(save_dir, exist_ok=True)
    if 2018 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/978-3-030-01246-5',
                'https://link.springer.com/book/10.1007/978-3-030-01216-8',
                'https://link.springer.com/book/10.1007/978-3-030-01219-9',
                'https://link.springer.com/book/10.1007/978-3-030-01225-0',
                'https://link.springer.com/book/10.1007/978-3-030-01228-1',
                'https://link.springer.com/book/10.1007/978-3-030-01231-1',
                'https://link.springer.com/book/10.1007/978-3-030-01234-2',
                'https://link.springer.com/book/10.1007/978-3-030-01237-3',
                'https://link.springer.com/book/10.1007/978-3-030-01240-3',
                'https://link.springer.com/book/10.1007/978-3-030-01249-6',
                'https://link.springer.com/book/10.1007/978-3-030-01252-6',
                'https://link.springer.com/book/10.1007/978-3-030-01258-8',
                'https://link.springer.com/book/10.1007/978-3-030-01261-8',
                'https://link.springer.com/book/10.1007/978-3-030-01264-9',
                'https://link.springer.com/book/10.1007/978-3-030-01267-0',
                'https://link.springer.com/book/10.1007/978-3-030-01270-0'
            ]
        else:
            urls_list = [
                'https://link.springer.com/book/10.1007/978-3-030-11009-3',
                'https://link.springer.com/book/10.1007/978-3-030-11012-3',
                'https://link.springer.com/book/10.1007/978-3-030-11015-4',
                'https://link.springer.com/book/10.1007/978-3-030-11018-5',
                'https://link.springer.com/book/10.1007/978-3-030-11021-5',
                'https://link.springer.com/book/10.1007/978-3-030-11024-6'
            ]
    elif 2016 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007%2F978-3-319-46448-0',
                'https://link.springer.com/book/10.1007%2F978-3-319-46475-6',
                'https://link.springer.com/book/10.1007%2F978-3-319-46487-9',
                'https://link.springer.com/book/10.1007%2F978-3-319-46493-0',
                'https://link.springer.com/book/10.1007%2F978-3-319-46454-1',
                'https://link.springer.com/book/10.1007%2F978-3-319-46466-4',
                'https://link.springer.com/book/10.1007%2F978-3-319-46478-7',
                'https://link.springer.com/book/10.1007%2F978-3-319-46484-8'
            ]
        else:
            urls_list = [
                'https://link.springer.com/book/10.1007%2F978-3-319-46604-0',
                'https://link.springer.com/book/10.1007%2F978-3-319-48881-3',
                'https://link.springer.com/book/10.1007%2F978-3-319-49409-8'
            ]
    elif 2014 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/978-3-319-10590-1',
                'https://link.springer.com/book/10.1007/978-3-319-10605-2',
                'https://link.springer.com/book/10.1007/978-3-319-10578-9',
                'https://link.springer.com/book/10.1007/978-3-319-10593-2',
                'https://link.springer.com/book/10.1007/978-3-319-10602-1',
                'https://link.springer.com/book/10.1007/978-3-319-10599-4',
                'https://link.springer.com/book/10.1007/978-3-319-10584-0'
            ]
        else:
            urls_list = [
                'https://link.springer.com/book/10.1007/978-3-319-16178-5',
                'https://link.springer.com/book/10.1007/978-3-319-16181-5',
                'https://link.springer.com/book/10.1007/978-3-319-16199-0',
                'https://link.springer.com/book/10.1007/978-3-319-16220-1'
            ]
    elif 2012 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/978-3-642-33718-5',
                'https://link.springer.com/book/10.1007/978-3-642-33709-3',
                'https://link.springer.com/book/10.1007/978-3-642-33712-3',
                'https://link.springer.com/book/10.1007/978-3-642-33765-9',
                'https://link.springer.com/book/10.1007/978-3-642-33715-4',
                'https://link.springer.com/book/10.1007/978-3-642-33783-3',
                'https://link.springer.com/book/10.1007/978-3-642-33786-4'
            ]
        else:
            urls_list = [
                'https://link.springer.com/book/10.1007/978-3-642-33863-2',
                'https://link.springer.com/book/10.1007/978-3-642-33868-7',
                'https://link.springer.com/book/10.1007/978-3-642-33885-4'
            ]
    elif 2010 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/978-3-642-15549-9',
                'https://link.springer.com/book/10.1007/978-3-642-15552-9',
                'https://link.springer.com/book/10.1007/978-3-642-15558-1',
                'https://link.springer.com/book/10.1007/978-3-642-15561-1',
                'https://link.springer.com/book/10.1007/978-3-642-15555-0',
                'https://link.springer.com/book/10.1007/978-3-642-15567-3'
            ]
        else:
            urls_list = [
                'https://link.springer.com/book/10.1007/978-3-642-35749-7',
                'https://link.springer.com/book/10.1007/978-3-642-35740-4'
            ]
    elif 2008 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/978-3-540-88682-2',
                'https://link.springer.com/book/10.1007/978-3-540-88688-4',
                'https://link.springer.com/book/10.1007/978-3-540-88690-7',
                'https://link.springer.com/book/10.1007/978-3-540-88693-8'
            ]
        else:
            urls_list = []
    elif 2006 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/11744023',
                'https://link.springer.com/book/10.1007/11744047',
                'https://link.springer.com/book/10.1007/11744078',
                'https://link.springer.com/book/10.1007/11744085'
            ]
        else:
            urls_list = [
                'https://link.springer.com/book/10.1007/11754336'
            ]
    elif 2004 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/b97865',
                'https://link.springer.com/book/10.1007/b97866',
                'https://link.springer.com/book/10.1007/b97871',
                'https://link.springer.com/book/10.1007/b97873'
            ]
        else:
            urls_list = [

            ]
    elif 2002 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/3-540-47969-4',
                'https://link.springer.com/book/10.1007/3-540-47967-8',
                'https://link.springer.com/book/10.1007/3-540-47977-5',
                'https://link.springer.com/book/10.1007/3-540-47979-1'
            ]
        else:
            urls_list = [

            ]
    elif 2000 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/3-540-45054-8',
                'https://link.springer.com/book/10.1007/3-540-45053-X'
            ]
        else:
            urls_list = [

            ]
    elif 1998 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/BFb0055655',
                'https://link.springer.com/book/10.1007/BFb0054729'
            ]
        else:
            urls_list = [

            ]
    elif 1996 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/BFb0015518',
                'https://link.springer.com/book/10.1007/3-540-61123-1'
            ]
        else:
            urls_list = [

            ]
    elif 1994 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/3-540-57956-7',
                'https://link.springer.com/book/10.1007/BFb0028329'
            ]
        else:
            urls_list = [

            ]
    elif 1992 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/3-540-55426-2'
            ]
        else:
            urls_list = [

            ]
    elif 1990 == year:
        if not is_workshops:
            urls_list = [
                'https://link.springer.com/book/10.1007/BFb0014843'
            ]
        else:
            urls_list = [

            ]
    else:
        raise ValueError(f'ECCV {year} is current not available!')
    for url in urls_list:
        __download_from_springer(
            url, save_dir, year, is_workshops=is_workshops,
            time_sleep_in_seconds=time_sleep_in_seconds,
            downloader=downloader)


def __download_from_springer(
        url, save_dir, year, is_workshops=False, time_sleep_in_seconds=5,
        downloader='IDM'):
    downloader = Downloader(downloader)
    for i in range(3):
        try:
            papers_dict = springer.get_paper_name_link_from_url(url)
            break
        except Exception as e:
            print(str(e))
    # total_paper_number = len(papers_dict)
    pbar = tqdm(papers_dict.keys())
    postfix = f'ECCV_{year}'
    if is_workshops:
        postfix = f'ECCV_WS_{year}'

    for name in pbar:
        pbar.set_description(f'Downloading paper {name}')
        if not os.path.exists(os.path.join(save_dir, f'{name}_{postfix}.pdf')):
            downloader.download(
                papers_dict[name],
                os.path.join(save_dir, f'{name}_{postfix}.pdf'),
                time_sleep_in_seconds)


if __name__ == '__main__':
    year = 2024
    # total_paper_number = 2387
    total_paper_number = save_csv(year)
    download_from_csv(year,
                      save_dir=fr'Z:\all_papers\ECCV\ECCV_{year}',
                      is_download_supplement=True,
                      time_step_in_seconds=5,
                      total_paper_number=total_paper_number,
                      is_workshops=False)
    # move_main_and_supplement_2_one_directory(
    #     main_path=f'E:\\ECCV_{year}\\main_paper',
    #     supplement_path=f'E:\\ECCV_{year}\\supplement',
    #     supp_pdf_save_path=f'E:\\ECCV_{year}\\main_paper'
    # )
    # for year in range(2018, 2017, -2):
    #     # download_from_springer(
    #     #     save_dir=f'F:\\ECCV_{year}',
    #     #     year=year,
    #     #     is_workshops=False, time_sleep_in_seconds=30)
    #     download_from_springer(
    #         save_dir=f'F:\\ECCV_WS_{year}',
    #         year=year,
    #         is_workshops=True, time_sleep_in_seconds=30)
    # pass
