"""paper_downloader_NIPS.py"""

import urllib
import time
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
from lib.downloader import Downloader
from lib import csv_process
from lib.openreview import download_nips_papers_given_url
from lib.my_request import urlopen_with_retry


def save_csv(year):
    """
    write nips papers' and supplemental material's urls in one csv file
    :param year: int
    :return: num_download: int, the total number of papers.
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_file_pathname = os.path.join(
        project_root_folder, 'csv', f'NIPS_{year}.csv'
    )
    with open(csv_file_pathname, 'w', newline='') as csvfile:
        fieldnames = ['title', 'main link', 'supplemental link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
                'Gecko/20100101 Firefox/23.0'}
        init_url = f'https://proceedings.neurips.cc/paper/{year}'
        dat_file_pathname = os.path.join(
            project_root_folder, 'urls', f'init_url_nips_{year}.dat')
        if os.path.exists(dat_file_pathname):
            with open(dat_file_pathname, 'rb') as f:
                content = pickle.load(f)
        else:
            content = urlopen_with_retry(url=init_url, headers=headers)
            with open(dat_file_pathname, 'wb') as f:
                pickle.dump(content, f)
        soup = BeautifulSoup(content, 'html.parser')
        paper_list = soup.find(
            'div', {'class': 'container-fluid'}).find_all('li')
        # num_download = 5 # number of papers to download
        num_download = len(paper_list)
        paper_list_bar = tqdm(zip(paper_list, range(num_download)))
        for paper in tqdm(zip(paper_list, range(num_download))):
            paper_dict = {'title': '',
                          'main link': '',
                          'supplemental link': ''}
            # get title
            # print('\n')
            this_paper = paper[0]
            title = slugify(this_paper.a.text)
            paper_dict['title'] = title
            # print('Downloading paper {}/{}: {}'.format(
            # paper[1] + 1, num_download, title))
            paper_list_bar.set_description(
                'Tracing paper {}/{}: {}'.format(
                    paper[1] + 1, num_download, title))

            # get abstract page url
            url2 = this_paper.a.get('href')
            abs_url = urllib.parse.urljoin(init_url, url2)
            abs_content = urlopen_with_retry(url=abs_url, headers=headers,
                                             raise_error_if_failed=False)
            if abs_content is not None:
                soup_temp = BeautifulSoup(abs_content, 'html.parser')
                # abstract = soup_temp.find(
                # 'p', {'class': 'abstract'}).text.strip()
                # paper_dict[title] = abstract
                all_a = soup_temp.findAll('a')
                for a in all_a:
                    # print(a.text[:-2])
                    # print(a.text[:-2].strip().lower())
                    if 'paper' == a.text[:-2].strip().lower():
                        paper_dict['main link'] = urllib.parse.urljoin(
                            abs_url, a.get('href'))
                    elif 'supplemental' == a.text[:-2].strip().lower():
                        paper_dict['supplemental link'] = \
                            urllib.parse.urljoin(abs_url, a.get('href'))
                        break
            else:
                print('Error: ' + title)
                if paper_dict['main link'] == '':
                    paper_dict['main link'] = 'error'
                if paper_dict['supplemental link'] == '':
                    paper_dict['supplemental link'] = 'error'
            writer.writerow(paper_dict)
            time.sleep(1)
    return num_download


def download_from_csv(
        year, save_dir, is_download_mainpaper=True, is_download_supplement=True,
        time_step_in_seconds=5, total_paper_number=None, downloader='IDM'):
    """
    download all NIPS paper and supplement files given year, restore in
    save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, NIPS year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_mainpaper: boot, True for downloading main papers
    :param is_download_supplement: bool, True for downloading supplemental
        material
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds
    :param total_paper_number: int, the total number of papers that is going to
        download
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder', default to 'IDM'
    :return: True
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    postfix = f'NIPS_{year}'
    csv_file_path = os.path.join(project_root_folder, 'csv', f'NIPS_{year}.csv')
    return csv_process.download_from_csv(
        postfix=postfix,
        save_dir=save_dir,
        csv_file_path=csv_file_path,
        is_download_supplement=is_download_supplement,
        time_step_in_seconds=time_step_in_seconds,
        total_paper_number=total_paper_number,
        downloader=downloader
    )


# def rename_supp( year, supp_dir):
#     """
#     rename supplemental material
#     :param year: int, NIPS year, such 2019
#     :param supp_dir: str, supplement material's save path
#     :return: True
#     """
#     if not os.path.exists(supp_dir):
#         raise ValueError(f'''can't find path {supp_dir}''')
#
#     postfix = f'NIPS_{year}'
#     with open(f'..\\csv\\NIPS_{year}.csv', newline='') as csvfile:
#         myreader = csv.DictReader(csvfile, delimiter=',')
#         pbar = tqdm(myreader)
#         for this_paper in pbar:
#             title = slugify(this_paper['title'])
#             this_paper_supp_path_no_ext = os.path.join(
#             supp_dir, f'{title}_{postfix}_supp.')
#
#             if '' != this_paper['supplemental link']:
#                 supp_ori_name = this_paper['supplemental link'].split('/')[-1]
#                 supp_type = supp_ori_name.split('.')[-1]
#                 if os.path.exists(os.path.join(supp_dir, supp_ori_name)) and \
#                 not os.path.exists(
#                         this_paper_supp_path_no_ext + supp_type):
#                     os.rename(
#                         os.path.join(supp_dir, supp_ori_name),
#                         this_paper_supp_path_no_ext + supp_type
#                     )
#                 pbar.set_description(f'Renaming paper: {title}...')


if __name__ == '__main__':
    year = 2024
    # total_paper_number = 1899
    # total_paper_number = save_csv(year)
    # download_from_csv(
    #     year, f'..\\NIPS_{year}',
    #     is_download_mainpaper=False,
    #     is_download_supplement=True,
    #     time_step_in_seconds=20,
    #     total_paper_number=total_paper_number,
    #     downloader='IDM')
    download_nips_papers_given_url(
        save_dir=rf'E:\NIPS_{year}',
        year=year,
        base_url=f'https://openreview.net/group?id=NeurIPS.cc/'
                 f'{year}/Conference',
        time_step_in_seconds=10,
        # download_groups=['poster'],
        downloader='IDM')
    # move_main_and_supplement_2_one_directory(
    #     main_path=rf'F:\workspace\python3_ws\paper_downloader-master\NIPS_{year}\main_paper',
    #     supplement_path=rf'F:\workspace\python3_ws\paper_downloader-master\NIPS_{year}\supplement',
    #     supp_pdf_save_path=rf'F:\workspace\python3_ws\paper_downloader-master\NIPS_{year}\supplement_pdf'
    # )
