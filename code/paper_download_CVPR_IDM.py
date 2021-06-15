"""paper_download_CVPR_IDM.py"""

import urllib
from urllib.request import urlopen
import time
from bs4 import BeautifulSoup
import pickle
from PyPDF3 import PdfFileMerger
import zipfile
import os
import shutil
from tqdm import tqdm
import subprocess
from slugify import slugify
import csv
import lib.IDM as IDM
import lib.thunder as Thunder
from lib.supplement_porcess import merge_main_supplement, move_main_and_supplement_2_one_directory, \
    move_main_and_supplement_2_one_directory_with_group


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
        if os.path.exists(f'..\\urls\\init_url_CVPR_{year}.dat'):
            with open(f'..\\urls\\init_url_CVPR_{year}.dat', 'rb') as f:
                content = pickle.load(f)
        else:
            content = urlopen(init_url).read()
            # content = open(f'..\\CVPR_{year}.html', 'rb').read()
            with open(f'..\\urls\\init_url_CVPR_{year}.dat', 'wb') as f:
                pickle.dump(content, f)
        soup = BeautifulSoup(content, 'html5lib')
        paper_list_bar = tqdm(soup.find('div', {'id': 'content'}).find_all(['dd', 'dt']))
        paper_index = 0
        paper_dict = {'title': '',
                      'main link': '',
                      'supplemental link': ''}
        for paper in paper_list_bar:
            is_new_paper = False

            # get title
            try:
                if 'dt' == paper.name and 'ptitle' == paper.get('class')[0]:  # title:
                    title = slugify(paper.text.strip())
                    paper_dict['title'] = title
                    paper_index += 1
                    paper_list_bar.set_description_str(f'Downloading paper {paper_index}: {title}')
                elif 'dd' == paper.name:
                    all_as = paper.find_all('a')
                    for a in all_as:
                        if 'pdf' == slugify(a.text.strip()):
                            main_link = urllib.parse.urljoin(init_url, a.get('href'))
                            paper_dict['main link'] = main_link
                            is_new_paper = True
                        elif 'supp' == slugify(a.text.strip()):
                            supp_link = urllib.parse.urljoin(init_url, a.get('href'))
                            paper_dict['supplemental link'] = supp_link
                            break
            except:
                pass
            if is_new_paper:
                writer.writerow(paper_dict)
                paper_dict = {'title': '',
                              'main link': '',
                              'supplemental link': ''}
    return paper_index


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

        init_url = f'http://openaccess.thecvf.com/CVPR{year}_workshops/menu'
        if os.path.exists(f'..\\urls\\init_url_CVPR_WS_{year}.dat'):
            with open(f'..\\urls\\init_url_CVPR_WS_{year}.dat', 'rb') as f:
                content = pickle.load(f)
        else:
            content = urlopen(init_url).read()
            # content = open(f'..\\CVPR_WS_{year}.html', 'rb').read()
            with open(f'..\\urls\\init_url_CVPR_WS_{year}.dat', 'wb') as f:
                pickle.dump(content, f)
        soup = BeautifulSoup(content, 'html5lib')
        paper_group_list_bar = soup.find('div', {'id': 'content'}).find_all('dd')
        paper_index = 0
        paper_dict = {'group': '',
                      'title': '',
                      'main link': '',
                      'supplemental link': ''}
        for group in paper_group_list_bar:
            # get group name
            a = group.find('a')
            group_name = slugify(a.text)
            paper_dict['group'] = group_name
            print(f'GROUP: {group_name}')
            group_link = urllib.parse.urljoin(init_url, a.get('href'))
            group_content = urlopen(group_link).read()
            group_soup = BeautifulSoup(group_content, 'html5lib')
            paper_list_bar = tqdm(group_soup.find('div', {'id': 'content'}).find_all(['dd', 'dt']))
            for paper in paper_list_bar:
                is_new_paper = False

                # get title
                try:
                    if 'dt' == paper.name and 'ptitle' == paper.get('class')[0]:  # title:
                        title = slugify(paper.text.strip())
                        paper_dict['title'] = title
                        paper_index += 1
                        paper_list_bar.set_description_str(f'Downloading paper {paper_index}: {title}')
                    elif 'dd' == paper.name:
                        all_as = paper.find_all('a')
                        for a in all_as:
                            if 'pdf' == slugify(a.text.strip()):
                                main_link = urllib.parse.urljoin(group_link, a.get('href'))
                                paper_dict['main link'] = main_link
                                is_new_paper = True
                            elif 'supp' == slugify(a.text.strip()):
                                supp_link = urllib.parse.urljoin(init_url, a.get('href'))
                                paper_dict['supplemental link'] = supp_link
                                break
                except:
                    pass
                if is_new_paper:
                    writer.writerow(paper_dict)
                    paper_dict = {'group': group_name,
                                  'title': '',
                                  'main link': '',
                                  'supplemental link': ''}
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
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :param total_paper_number: int, the total number of papers that is going to download
    :param is_workshops: bool, is to download workshops from csv file.
    :param downloader: str, the downloader to download, could be 'IDM' or 'Thunder', default to 'IDM'.
    :return: True
    """
    main_save_path = os.path.join(save_dir, 'main_paper')
    supplement_save_path = os.path.join(save_dir, 'supplement')
    os.makedirs(main_save_path, exist_ok=True)
    os.makedirs(supplement_save_path, exist_ok=True)

    error_log = []
    postfix = f'CVPR_{year}'
    if is_workshops:
        postfix = f'CVPR_WS_{year}'
    csv_file_name = f'..\\csv\\CVPR_{year}.csv' if not is_workshops else f'..\\csv\\CVPR_WS_{year}.csv'
    with open(csv_file_name, newline='') as csvfile:
        myreader = csv.DictReader(csvfile, delimiter=',')
        pbar = tqdm(myreader)
        i = 0
        for this_paper in pbar:
            i += 1
            # get title
            if is_workshops:
                group = slugify(this_paper['group'])
            title = slugify(this_paper['title'])
            if total_paper_number is not None:
                pbar.set_description(f'Downloading paper {i}/{total_paper_number}')

            else:
                pbar.set_description(f'Downloading paper {i}')

            this_paper_main_path = os.path.join(main_save_path, f'{title}_{postfix}.pdf')
            if is_workshops:
                this_paper_main_path = os.path.join(main_save_path, group, f'{title}_{postfix}.pdf')
            this_paper_supp_path_no_ext = os.path.join(supplement_save_path, f'{title}_{postfix}_supp.')
            if is_workshops:
                this_paper_supp_path_no_ext = os.path.join(supplement_save_path, group, f'{title}_{postfix}_supp.')
            if is_download_supplement:
                if '' != this_paper['supplemental link'] and os.path.exists(this_paper_main_path) and \
                        (os.path.exists(this_paper_supp_path_no_ext + 'zip') or os.path.exists(
                            this_paper_supp_path_no_ext + 'pdf')):
                    continue
                elif '' == this_paper['supplemental link'] and os.path.exists(this_paper_main_path):
                    continue
            else:
                if os.path.exists(this_paper_main_path):
                    continue
            if 'error' == this_paper['main link']:
                error_log.append((title, 'no MAIN link'))
            elif '' != this_paper['main link']:
                if is_workshops:
                    os.makedirs(os.path.join(main_save_path, group), exist_ok=True)
                    if is_download_supplement:
                        os.makedirs(os.path.join(supplement_save_path, group), exist_ok=True)
                try:
                    # download paper with IDM
                    if not os.path.exists(this_paper_main_path):
                        if 'IDM' == downloader:
                            IDM.download(
                                urls=this_paper['main link'].replace(' ', '%20'),
                                save_path=os.path.join(os.getcwd(), this_paper_main_path),
                                time_sleep_in_seconds=time_step_in_seconds
                            )
                        elif 'Thunder' == downloader:
                            Thunder.download(
                                urls=this_paper['main link'].replace(' ', '%20'),
                                save_path=os.path.join(os.getcwd(), this_paper_main_path),
                                time_sleep_in_seconds=time_step_in_seconds
                            )
                        else:
                            raise ValueError(
                                f'''ERROR: Unsupported downloader: {downloader}, we currently only support'''
                                f''' "IDM" or "Thunder" ''')
                except Exception as e:
                    # error_flag = True
                    print('Error: ' + title + ' - ' + str(e))
                    error_log.append((title, this_paper['main link'], 'main paper download error', str(e)))
                # download supp
                if is_download_supplement:
                    # check whether the supp can be downloaded
                    if not (os.path.exists(this_paper_supp_path_no_ext + 'zip') or
                            os.path.exists(this_paper_supp_path_no_ext + 'pdf')):
                        if 'error' == this_paper['supplemental link']:
                            error_log.append((title, 'no SUPPLEMENTAL link'))
                        elif '' != this_paper['supplemental link']:
                            supp_type = this_paper['supplemental link'].split('.')[-1]
                            try:
                                if 'IDM' == downloader:
                                    IDM.download(
                                        urls=this_paper['supplemental link'],
                                        save_path=os.path.join(os.getcwd(), this_paper_supp_path_no_ext+supp_type),
                                        time_sleep_in_seconds=time_step_in_seconds
                                    )
                                elif 'Thunder' == downloader:
                                    Thunder.download(
                                        urls=this_paper['supplemental link'],
                                        save_path=os.path.join(os.getcwd(), this_paper_supp_path_no_ext+supp_type),
                                        time_sleep_in_seconds=time_step_in_seconds
                                    )
                                else:
                                    raise ValueError(
                                        f'''ERROR: Unsupported downloader: {downloader}, we currently only support'''
                                        f''' "IDM" or "Thunder" ''')
                            except Exception as e:
                                # error_flag = True
                                print('Error: ' + title + ' - ' + str(e))
                                error_log.append((title, this_paper['supplemental link'], 'supplement download error',
                                                  str(e)))

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
    year = 2021
    # total_paper_number = save_csv_workshops(year)
    # total_paper_number = 517
    # total_paper_number = save_csv(year)
    # download_from_csv(year,
    #                   save_dir=fr'D:\CVPR_WS_{year}',
    #                   is_download_supplement=True,
    #                   time_step_in_seconds=2,
    #                   total_paper_number=total_paper_number,
    #                   is_workshops=True)
    # move_main_and_supplement_2_one_directory(
    #     main_path=rf'D:\CVPR_{year}\main_paper',
    #     supplement_path=rf'D:\CVPR_{year}\supplement',
    #     supp_pdf_save_path=rf'D:\CVPR_{year}\main_paper'
    # )
    move_main_and_supplement_2_one_directory_with_group(
        main_path=rf'D:\CVPR_WS_{year}\main_paper',
        supplement_path=rf'D:\CVPR_WS_{year}\supplement',
        supp_pdf_save_path=rf'D:\CVPR_WS_{year}\main_paper'
    )
    pass