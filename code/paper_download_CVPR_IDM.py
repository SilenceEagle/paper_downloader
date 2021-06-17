"""paper_download_CVPR_IDM.py"""

import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pickle
import os
from slugify import slugify
import csv
from lib.supplement_porcess import merge_main_supplement, move_main_and_supplement_2_one_directory, \
    move_main_and_supplement_2_one_directory_with_group
from lib.cvf import get_paper_dict_list
from lib import csv_process


def save_csv(year):
    """
    write CVPR conference papers' and supplemental material's urls in one csv file
    :param year: int
    :return: True
    """
    with open(f'..\\csv\\CVPR_{year}.csv', 'w', newline='') as csvfile:
        fieldnames = ['title', 'main link', 'supplemental link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        if year == 2021:
            init_url = f'https://openaccess.thecvf.com/CVPR{year}?day=all'
        else:
            init_url = f'http://openaccess.thecvf.com/CVPR{year}.py'
        content = None
        if os.path.exists(f'..\\urls\\init_url_CVPR_{year}.dat'):
            with open(f'..\\urls\\init_url_CVPR_{year}.dat', 'rb') as f:
                content = pickle.load(f)
        paper_dict_list, content = get_paper_dict_list(
            url=init_url,
            content=content)
        if not os.path.exists(f'..\\urls\\init_url_CVPR_{year}.dat'):
            with open(f'..\\urls\\init_url_CVPR_{year}.dat', 'wb') as f:
                pickle.dump(content, f)
        for paper_dict in paper_dict_list:
            writer.writerow(paper_dict)
    return len(paper_dict_list)


def save_csv_workshops(year):
    """
    write CVPR workshops papers' and supplemental material's urls in one csv file
    :param year: int
    :return: True
    """
    with open(f'..\\csv\\CVPR_WS_{year}.csv', 'w', newline='') as csvfile:
        fieldnames = ['group', 'title', 'main link', 'supplemental link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}

        init_url = f'http://openaccess.thecvf.com/CVPR{year}_workshops/menu'
        if os.path.exists(f'..\\urls\\init_url_CVPR_WS_{year}.dat'):
            with open(f'..\\urls\\init_url_CVPR_WS_{year}.dat', 'rb') as f:
                content = pickle.load(f)
        else:
            req = urllib.request.Request(url=init_url, headers=headers)
            content = urllib.request.urlopen(req, timeout=10).read()
            # content = open(f'..\\CVPR_WS_{year}.html', 'rb').read()
            with open(f'..\\urls\\init_url_CVPR_WS_{year}.dat', 'wb') as f:
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
                group_name=group_name
            )
            paper_index += len(group_paper_dict_list)
            for paper_dict in group_paper_dict_list:
                writer.writerow(paper_dict)
    return paper_index


def download_from_csv(
        year, save_dir, is_download_supplement=True, time_step_in_seconds=5, total_paper_number=None,
        is_workshops=False, downloader='IDM'):
    """
    download all CVPR paper and supplement files given year, restore in save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, CVPR year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental material
    :param time_step_in_seconds: int, the interval time between two downloading request in seconds
    :param total_paper_number: int, the total number of papers that is going to download
    :param is_workshops: bool, is to download workshops from csv file.
    :param downloader: str, the downloader to download, could be 'IDM' or 'Thunder', default to 'IDM'.
    :return: True
    """

    postfix = f'CVPR_{year}'
    if is_workshops:
        postfix = f'CVPR_WS_{year}'
    csv_file_path = f'..\\csv\\CVPR_{year}.csv' if not is_workshops else f'..\\csv\\CVPR_WS_{year}.csv'
    csv_process.download_from_csv(
        postfix=postfix,
        save_dir=save_dir,
        csv_file_path=csv_file_path,
        is_download_supplement=is_download_supplement,
        time_step_in_seconds=time_step_in_seconds,
        total_paper_number=total_paper_number,
        downloader=downloader
    )
    return True


def download_paper(
        year, save_dir, is_download_supplement=True, time_step_in_seconds=5, is_download_main_conference=True,
        is_download_workshops=True, downloader='IDM'):
    """
    download all CVPR pepers in given year, support downloading main conference and workshops.
    :param year: int, CVPR year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental material
    :param time_step_in_seconds: int, the interval time between two downloading request in seconds
    :param downloader: str, the downloader to download, could be 'IDM' or 'Thunder', default to 'IDM'.
    :return:
    """
    # main conference
    if is_download_main_conference:
        csv_file_path = f'..\\csv\\CVPR_{year}.csv'
        if not os.path.exists(csv_file_path):
            total_paper_number = save_csv(year=year)
        else:
            with open(csv_file_path, newline='') as csvfile:
                myreader = csv.DictReader(csvfile, delimiter=',')
                total_paper_number = sum(1 for row in myreader)

        download_from_csv(
            year=year,
            save_dir=os.path.join(save_dir, f'CVPR_{year}'),
            is_download_supplement=is_download_supplement,
            time_step_in_seconds=time_step_in_seconds,
            total_paper_number=total_paper_number,
            is_workshops=False,
            downloader=downloader
        )

    # workshops
    if is_download_workshops:
        csv_file_path = f'..\\csv\\CVPR_WS_{year}.csv'
        if not os.path.exists(csv_file_path):
            total_paper_number = save_csv(year=year)
        else:
            with open(csv_file_path, newline='') as csvfile:
                myreader = csv.DictReader(csvfile, delimiter=',')
                total_paper_number = sum(1 for row in myreader)
        download_from_csv(
            year=year,
            save_dir=os.path.join(save_dir, f'CVPR_WS_{year}'),
            is_download_supplement=is_download_supplement,
            time_step_in_seconds=time_step_in_seconds,
            total_paper_number=total_paper_number,
            is_workshops=True,
            downloader=downloader
        )


if __name__ == '__main__':
    year = 2021

    download_paper(
        year,
        save_dir=fr'D:\CVPR',
        is_download_supplement=True,
        time_step_in_seconds=5,
        is_download_main_conference=False,
        is_download_workshops=True
    )

    # move_main_and_supplement_2_one_directory(
    #     main_path=rf'D:\CVPR\CVPR_{year}\main_paper',
    #     supplement_path=rf'D:\CVPR\CVPR_{year}\supplement',
    #     supp_pdf_save_path=rf'D:\CVPR\CVPR_{year}\main_paper'
    # )
    # move_main_and_supplement_2_one_directory_with_group(
    #     main_path=rf'D:\CVPR\CVPR_WS_{year}\main_paper',
    #     supplement_path=rf'D:\CVPR\CVPR_WS_{year}\supplement',
    #     supp_pdf_save_path=rf'D:\CVPR\CVPR_WS_{year}\main_paper'
    # )
    pass