"""paper_download_ECCV_IDM.py"""

import urllib
from urllib.request import urlopen
import time
from bs4 import BeautifulSoup
import pickle
import os
from tqdm import tqdm
import subprocess
from slugify import slugify
import csv
from lib.supplement_porcess import move_main_and_supplement_2_one_directory


def save_csv(year):
    """
    write ECCV papers' and supplemental material's urls in one csv file
    :param year: int
    :return: True
    """
    with open(f'..\\csv\\ECCV_{year}.csv', 'w', newline='') as csvfile:
        fieldnames = ['title', 'main link', 'supplemental link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
        init_url = f'https://www.ecva.net/papers.php'
        if os.path.exists(f'..\\urls\\init_url_ECCV_{year}.dat'):
            with open(f'..\\urls\\init_url_ECCV_{year}.dat', 'rb') as f:
                content = pickle.load(f)
        else:
            req = urllib.request.Request(url=init_url, headers=headers)
            content = urllib.request.urlopen(req, timeout=10).read()
            # content = urlopen(init_url).read()
            # content = open(f'..\\ECCV_{year}.html', 'rb').read()
            with open(f'..\\urls\\init_url_ECCV_{year}.dat', 'wb') as f:
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
                if 'dt' == paper.name and 'ptitle' == paper.get('class')[0] and \
                        year == int(paper.a.get('href').split('_')[1][:4]):  # title:
                    # this_year = int(paper.a.get('href').split('_')[1][:4])
                    title = slugify(paper.text.strip())
                    paper_dict['title'] = title
                    paper_index += 1
                    paper_list_bar.set_description_str(f'Downloading paper {paper_index}: {title}')
                elif '' != paper_dict['title'] and 'dd' == paper.name:
                    all_as = paper.find_all('a')
                    for a in all_as:
                        if 'pdf' == slugify(a.text.strip()):
                            main_link = urllib.parse.urljoin(init_url, a.get('href'))
                            paper_dict['main link'] = main_link
                            is_new_paper = True
                        elif 'supp' == slugify(a.text.strip())[:4]:
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


def download_from_csv(
        year, save_dir, is_download_supplement=True, time_step_in_seconds=5, total_paper_number=None,
        is_workshops=False):
    """
    download all ECCV paper and supplement files given year, restore in save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, ECCV year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental material
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :param total_paper_number: int, the total number of papers that is going to download
    :param is_workshops: bool, is to download workshops from csv file.
    :return: True
    """
    main_save_path = os.path.join(save_dir, 'main_paper')
    supplement_save_path = os.path.join(save_dir, 'supplement')
    os.makedirs(main_save_path, exist_ok=True)
    os.makedirs(supplement_save_path, exist_ok=True)
    # use IDM to download everything
    idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'''  # should replace by the local IDM path
    basic_command = [idm_path, '/d', 'xxxx', '/p', 'xxx', '/f', 'xxxx', '/n']

    error_log = []
    postfix = f'ECCV_{year}'
    if is_workshops:
        postfix = f'ECCV_WS_{year}'
    csv_file_name = f'..\\csv\\ECCV_{year}.csv' if not is_workshops else f'..\\csv\\ECCV_WS_{year}.csv'
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
                        head, tail = os.path.split(this_paper_main_path)
                        basic_command[2] = this_paper['main link'].replace(' ', '%20')
                        basic_command[4] = head
                        basic_command[6] = tail
                        p = subprocess.Popen(' '.join(basic_command))
                        p.wait()
                        time.sleep(time_step_in_seconds)
                        # while True:
                        #     if os.path.exists(this_paper_main_path):
                        #         break
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
                                head, tail = os.path.split(this_paper_supp_path_no_ext)
                                basic_command[2] = this_paper['supplemental link']
                                basic_command[4] = head
                                basic_command[6] = tail + supp_type
                                p = subprocess.Popen(' '.join(basic_command))
                                p.wait()
                                time.sleep(time_step_in_seconds)
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
    year = 2020
    # total_paper_number = 1358
    # total_paper_number = save_csv(year)
    # download_from_csv(year,
    #                   save_dir=f'F:\\workspace\\python3_ws\\ECCV_{year}',
    #                   is_download_supplement=True,
    #                   time_step_in_seconds=5,
    #                   total_paper_number=total_paper_number,
    #                   is_workshops=False)
    move_main_and_supplement_2_one_directory(
        main_path=f'F:\\workspace\\python3_ws\\ECCV_{year}\\main_paper',
        supplement_path=f'F:\\workspace\\python3_ws\\ECCV_{year}\\supplement')

    pass