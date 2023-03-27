"""paper_downloader_CVF.py"""

import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pickle
import os
from slugify import slugify
import csv
import sys
root_folder = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
from lib.supplement_porcess import merge_main_supplement, move_main_and_supplement_2_one_directory, \
    move_main_and_supplement_2_one_directory_with_group
from lib.cvf import get_paper_dict_list
from lib import csv_process


def save_csv(year, conference):
    """
    write CVF conference papers' and supplemental material's urls in one csv file
    :param year: int
    :param conference: str, one of ['CVPR', 'ICCV', 'WACV', 'ACCV']
    :return: True
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if conference not in ['CVPR', 'ICCV', 'WACV', 'ACCV']:
        raise ValueError(f'{conference} is not found in '
                         f'https://openaccess.thecvf.com/menu, '
                         f'maybe a spelling mistake!')
    csv_file_pathname = os.path.join(
        project_root_folder, 'csv', f'{conference}_{year}.csv'
    )
    with open(csv_file_pathname, 'w', newline='') as csvfile:
        fieldnames = ['title', 'main link', 'supplemental link', 'arxiv']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        init_url = f'http://openaccess.thecvf.com/{conference}{year}'
        if conference == 'ICCV' and year == 2021:
            init_url = 'https://openaccess.thecvf.com/ICCV2021?day=all'
        elif conference == 'CVPR' and year == 2022:
            init_url = 'https://openaccess.thecvf.com/CVPR2022?day=all'
        content = None
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
        tmp_list = soup.find('div', {'id': 'content'}).find_all('dt')
        if len(tmp_list) <= 1:
            paper_different_days_list_bar = soup.find(
                'div', {'id': 'content'}).find_all('dd')
            paper_index = 0
            for group in paper_different_days_list_bar:
                # get group name
                a = group.find('a')
                print(a.text)
                group_link = urllib.parse.urljoin(init_url, a.get('href'))
                group_paper_dict_list, _ = get_paper_dict_list(
                    url=group_link
                )
                paper_index += len(group_paper_dict_list)
                for paper_dict in group_paper_dict_list:
                    writer.writerow(paper_dict)
            return paper_index
        else:
            paper_dict_list, content = get_paper_dict_list(
                url=init_url,
                content=content)
            for paper_dict in paper_dict_list:
                writer.writerow(paper_dict)
            return len(paper_dict_list)


def save_csv_workshops(year, conference):
    """
    write CVF workshops papers' and supplemental material's urls in one csv file
    :param year: int
    :param conference: str, one of ['CVPR', 'ICCV', 'WACV', 'ACCV']
    :return: True
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if conference not in ['CVPR', 'ICCV', 'WACV', 'ACCV']:
        raise ValueError(f'{conference} is not found in '
                         f'https://openaccess.thecvf.com/menu, '
                         f'maybe a spelling mistake!')
    csv_file_pathname = os.path.join(
        project_root_folder, 'csv', f'{conference}_WS_{year}.csv'
    )
    with open(csv_file_pathname, 'w', newline='') as csvfile:
        fieldnames = ['group', 'title', 'main link', 'supplemental link',
                      'arxiv']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
                'Gecko/20100101 Firefox/23.0'}

        init_url = f'https://openaccess.thecvf.com/' \
                   f'{conference}{year}_workshops/menu'
        url_file_pathname = os.path.join(
            project_root_folder, 'urls', f'init_url_{conference}_WS_{year}.dat'
        )
        if os.path.exists(url_file_pathname):
            with open(url_file_pathname, 'rb') as f:
                content = pickle.load(f)
        else:
            req = urllib.request.Request(url=init_url, headers=headers)
            content = urllib.request.urlopen(req, timeout=20).read()
            # content = open(f'..\\{conference}_WS_{year}.html', 'rb').read()
            with open(url_file_pathname, 'wb') as f:
                pickle.dump(content, f)
        soup = BeautifulSoup(content, 'html5lib')
        paper_group_list_bar = soup.find('div', {'id': 'content'}).find_all('dd')
        paper_index = 0
        for group in paper_group_list_bar:
            # get group name
            a = group.find('a')
            group_name = slugify(a.text)
            print(f'GROUP: {group_name}')
            group_link = urllib.parse.urljoin(init_url, a.get('href'))
            group_paper_dict_list, _ = get_paper_dict_list(
                url=group_link,
                group_name=group_name,
                timeout=20,
            )
            paper_index += len(group_paper_dict_list)
            for paper_dict in group_paper_dict_list:
                writer.writerow(paper_dict)
    return paper_index


def download_from_csv(
        year, conference, save_dir, is_download_main_paper=True,
        is_download_supplement=True, time_step_in_seconds=5,
        total_paper_number=None, is_workshops=False, downloader='IDM'):
    """
    download all CVF paper and supplement files given year, restore in
    save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, CVF year, such 2019
    :param conference: str, one of ['CVPR', 'ICCV', 'WACV']
    :param save_dir: str, paper and supplement material's save path
    :param is_download_main_paper: bool, True for downloading main paper
    :param is_download_supplement: bool, True for downloading supplemental
        material
    :param time_step_in_seconds: int, the interval time between two downloading
        request in seconds
    :param total_paper_number: int, the total number of papers that is going to
        download
    :param is_workshops: bool, is to download workshops from csv file.
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder', default to 'IDM'.
    :return: True
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    postfix = f'{conference}_{year}'
    if is_workshops:
        postfix = f'{conference}_WS_{year}'
    csv_file_path = os.path.join(
        project_root_folder,
        'csv',
        f'{conference}_{year}.csv' if not is_workshops else
        f'{conference}_WS_{year}.csv'
    )
    csv_process.download_from_csv(
        postfix=postfix,
        save_dir=save_dir,
        csv_file_path=csv_file_path,
        is_download_main_paper=is_download_main_paper,
        is_download_supplement=is_download_supplement,
        time_step_in_seconds=time_step_in_seconds,
        total_paper_number=total_paper_number,
        downloader=downloader
    )
    return True


def download_paper(
        year, conference, save_dir, is_download_main_paper=True,
        is_download_supplement=True, time_step_in_seconds=5,
        is_download_main_conference=True, is_download_workshops=True,
        downloader='IDM'):
    """
    download all CVF papers in given year, support downloading main conference
    and workshops.
    :param year: int, CVF year, such 2019.
    :param conference: str, one of {'CVPR', 'ICCV', 'WACV'}.
    :param save_dir: str, paper and supplement material's save path.
    :param is_download_main_paper: bool, True for downloading main paper.
    :param is_download_supplement: bool, True for downloading supplemental
        material.
    :param time_step_in_seconds: int, the interval time between two downloading
        request in seconds.
    :param is_download_main_conference: bool, this parameter controls whether to
        download main conference papers,
        it is a upper level control flag of parameters is_download_main_paper
        and is_download_supplement. eg. After setting
        is_download_main_conference=True, is_download_main_paper=False,
        is_download_supplement=True, the only the supplement materials of the
        conference (vs. workshops) will be downloaded.
    :param is_download_workshops: bool, True for downloading workshops paper
        and is similar with is_download_main_conference.
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder', default to 'IDM'.
    :return:
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # main conference
    if is_download_main_conference:
        csv_file_path = os.path.join(
            project_root_folder, 'csv', f'{conference}_{year}.csv')
        if not os.path.exists(csv_file_path):
            total_paper_number = save_csv(year=year, conference=conference)
        else:
            with open(csv_file_path, newline='') as csvfile:
                myreader = csv.DictReader(csvfile, delimiter=',')
                total_paper_number = sum(1 for row in myreader)

        download_from_csv(
            year=year,
            conference=conference,
            save_dir=os.path.join(save_dir, f'{conference}_{year}'),
            is_download_main_paper=is_download_main_paper,
            is_download_supplement=is_download_supplement,
            time_step_in_seconds=time_step_in_seconds,
            total_paper_number=total_paper_number,
            is_workshops=False,
            downloader=downloader
        )

    # workshops
    if is_download_workshops:
        csv_file_path = os.path.join(
            project_root_folder, 'csv', f'{conference}_WS_{year}.csv')
        if not os.path.exists(csv_file_path):
            total_paper_number = save_csv_workshops(
                year=year, conference=conference)
        else:
            with open(csv_file_path, newline='') as csvfile:
                myreader = csv.DictReader(csvfile, delimiter=',')
                total_paper_number = sum(1 for row in myreader)
        download_from_csv(
            year=year,
            conference=conference,
            save_dir=os.path.join(save_dir, f'{conference}_WS_{year}'),
            is_download_main_paper=is_download_main_paper,
            is_download_supplement=is_download_supplement,
            time_step_in_seconds=time_step_in_seconds,
            total_paper_number=total_paper_number,
            is_workshops=True,
            downloader=downloader
        )


if __name__ == '__main__':
    year = 2023
    conference = 'WACV'
    # download_paper(
    #     year,
    #     conference=conference,
    #     save_dir=fr'E:\{conference}',
    #     is_download_main_paper=True,
    #     is_download_supplement=True,
    #     time_step_in_seconds=5,
    #     is_download_main_conference=True,
    #     is_download_workshops=True
    # )
    #
    move_main_and_supplement_2_one_directory(
        main_path=rf'E:\{conference}\{conference}_{year}\main_paper',
        supplement_path=rf'E:\{conference}\{conference}_{year}\supplement',
        supp_pdf_save_path=rf'E:\{conference}\{conference}_{year}\main_paper'
    )
    move_main_and_supplement_2_one_directory_with_group(
        main_path=rf'E:\{conference}\{conference}_WS_{year}\main_paper',
        supplement_path=rf'E:\{conference}\{conference}_WS_{year}\supplement',
        supp_pdf_save_path=rf'E:\{conference}\{conference}_WS_{year}\main_paper'
    )
    pass
