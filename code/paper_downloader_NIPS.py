"""paper_downloader_NIPS.py"""

import urllib
from urllib.request import urlopen
import time
from bs4 import BeautifulSoup
import pickle
import os
from tqdm import tqdm
from slugify import slugify
import csv
from lib.supplement_porcess import move_main_and_supplement_2_one_directory
from lib.downloader import Downloader
from lib import csv_process
from lib.openreview import download_nips_papers_given_url


# def download_paper_and_sup_IDM(year, save_dir, is_download_supplement=True):
#     """
#     download all NIPS paper and supplement files given year, restore in save_dir/main_paper and save_dir/supplement
#     respectively
#     :param year: int, NIPS year, such 2019
#     :param save_dir: str, paper and supplement material's save path
#     :param is_download_supplement: bool, True for downloading supplemental material
#     :return: True
#     """
#     init_url = f'http://papers.nips.cc/book/advances-in-neural-information-processing-systems-{year-1987}-{year}'
#     main_save_path = os.path.join(save_dir, 'main_paper')
#     supplement_save_path = os.path.join(save_dir, 'supplement')
#     os.makedirs(main_save_path, exist_ok=True)
#     os.makedirs(supplement_save_path, exist_ok=True)
#     # use IDM to download everything
#     idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'''  # should replace by the local IDM path
#     basic_command = [idm_path, '/d', 'xxxx', '/p', os.getcwd(), '/f', 'xxxx', '/n']
#     # create current dict
#     title_list = []
#     # paper_dict = dict()
#
#     paper_website = 'http://papers.nips.cc'
#     postfix = f'NIPS_{year}'
#     if os.path.exists(f'..\\urls\\init_url_nips_{year}.dat'):
#         with open(f'..\\urls\\init_url_nips_{year}.dat', 'rb') as f:
#             content = pickle.load(f)
#     else:
#         content = urlopen(init_url).read()
#         with open(f'..\\urls\\init_url_nips_{year}.dat', 'wb') as f:
#             pickle.dump(content, f)
#     soup = BeautifulSoup(content, 'html.parser')
#     temp_soup = soup.find_all('ul')[1]  # after the book section
#     paper_list = temp_soup.find_all('li')
#     error_log = []
#     # num_download = 5 # number of papers to download
#     num_download = len(paper_list)
#     for paper in tqdm(zip(paper_list, range(num_download))):
#         # get title
#         print('\n')
#         this_paper = paper[0]
#         title = slugify(this_paper.a.text)
#         try:
#             print('Downloading paper {}/{}: {}'.format(paper[1]+1, num_download, title))
#         except:
#             print(title.encode('utf8'))
#         title_list.append(title)
#
#         # try:
#         #     asc_title = title.encode('utf-8').decode('ascii')
#         # except:
#         #     print('has non english characters, canceled!')
#         #     continue
#
#         this_paper_main_path = os.path.join(main_save_path, f'{title}_{postfix}.pdf')
#         this_paper_supp_path_no_ext = os.path.join(supplement_save_path, f'{title}_{postfix}_supp.')
#         if is_download_supplement:
#             if os.path.exists(this_paper_main_path) and \
#                 (os.path.exists(this_paper_supp_path_no_ext+'zip') or os.path.exists(this_paper_supp_path_no_ext+'pdf')):
#                 continue
#         else:
#             if os.path.exists(this_paper_main_path):
#                 continue
#
#         # get abstract page url
#         url2 = this_paper.a.get('href')
#
#         # try 1 time
#         # error_flag = False
#         timeout_seconds = 50
#         for d_iter in range(1):
#             try:
#                 abs_content = urlopen(paper_website + url2, timeout=timeout_seconds).read()
#                 soup_temp = BeautifulSoup(abs_content, 'html.parser')
#                 # abstract = soup_temp.find('p', {'class': 'abstract'}).text.strip()
#                 # paper_dict[title] = abstract
#                 all_a = soup_temp.findAll('a')
#                 paper_link = None
#                 supp_link = None
#                 for a in all_a[4:]:
#                     if '[PDF]' == a.text:
#                         paper_link = a.get('href')
#                     elif '[Supplemental]' == a.text:
#                         supp_link = a.get('href')
#                         supp_type = supp_link.split('.')[-1]
#                         break
#                 # paper_link = soup_temp.findAll('a')[4].get('href')
#                 # supp_link = soup_temp.findAll('a')[6].get('href')
#                 # supp_type = supp_link.split('.')[-1]
#             except Exception as e:
#                 error_flag = True
#                 print('Error: ' + title + ' - ' + str(e))
#                 error_log.append((title, paper_website + url2, 'main paper url error',str(e)))
#                 continue
#             try:
#                 # download paper with IDM
#                 if not os.path.exists(this_paper_main_path):
#                     basic_command[2] = paper_website + paper_link
#                     basic_command[6] = this_paper_main_path
#                     p = subprocess.Popen(' '.join(basic_command))
#                     p.wait()
#                     time.sleep(3)
#                     # while True:
#                     #     if os.path.exists(this_paper_main_path):
#                     #         break
#             except Exception as e:
#                 # error_flag = True
#                 print('Error: ' + title + ' - ' + str(e))
#                 error_log.append((title, paper_website + url2, 'main paper download error', str(e)))
#             # download supp
#             if is_download_supplement:
#                 # check whether the supp can be downloaded
#                 if not (os.path.exists(this_paper_supp_path_no_ext + 'zip') or
#                         os.path.exists(this_paper_supp_path_no_ext + 'pdf')):
#                     # try:
#                     #     req = urlopen(paper_website + supp_link, None, timeout_seconds)  # 5 seconds timeout
#                     #     no_supp = False
#                     # except Exception as e:
#                     #     try:
#                     #         no_supp = e.code == 404
#                     #     except:
#                     #         # error_flag = True
#                     #         print('Error: ' + title + ' - ' + str(e))
#                     #         error_log.append((title, paper_website + supp_link, 'supplement url error', str(e)))
#                     #         continue
#                     try:
#                         # if not no_supp:
#                         if supp_link is not None:
#                             basic_command[2] = paper_website + supp_link
#                             basic_command[6] = this_paper_supp_path_no_ext + supp_type
#                             p = subprocess.Popen(' '.join(basic_command))
#                             p.wait()
#                             time.sleep(3)
#                             # while True:
#                             #     if os.path.exists(this_paper_supp_path_no_ext + supp_type):
#                             #         break
#                     except Exception as e:
#                         # error_flag = True
#                         print('Error: ' + title + ' - ' + str(e))
#                         error_log.append((title, paper_website + supp_link, 'supplement download error', str(e)))
#
#         # if error_flag:
#         #     # paper_dict[title] = '\n'
#         #     error_log.append((title, paper_website + url2))
#
#     # store the results
#     # 1. store in the pickle file
#     # with open(f'{postfix}_pre.dat', 'wb') as f:
#     #     pickle.dump(paper_dict, f)
#
#     # 2. write error log
#     print('write error log')
#     with open('..\\log\\download_err_log.txt', 'w') as f:
#         for log in tqdm(error_log):
#             for e in log:
#                 if e is not None:
#                     f.write(e)
#                 else:
#                     f.write('None')
#                 f.write('\n')
#
#             f.write('\n')


def save_csv(year):
    """
    write nips papers' and supplemental material's urls in one csv file
    :param year: int
    :return: num_download: int, the total number of papers.
    """
    with open(f'..\\csv\\NIPS_{year}.csv', 'w', newline='') as csvfile:
        fieldnames = ['title', 'main link', 'supplemental link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
        init_url = f'https://proceedings.neurips.cc/paper/{year}'

        if os.path.exists(f'..\\urls\\init_url_nips_{year}.dat'):
            with open(f'..\\urls\\init_url_nips_{year}.dat', 'rb') as f:
                content = pickle.load(f)
        else:
            req = urllib.request.Request(url=init_url, headers=headers)
            content = urllib.request.urlopen(req, timeout=10).read()
            with open(f'..\\urls\\init_url_nips_{year}.dat', 'wb') as f:
                pickle.dump(content, f)
        soup = BeautifulSoup(content, 'html.parser')
        paper_list = soup.find('div', {'class': 'container-fluid'}).find_all('li')
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
            # print('Downloading paper {}/{}: {}'.format(paper[1] + 1, num_download, title))
            paper_list_bar.set_description('Tracing paper {}/{}: {}'.format(paper[1] + 1, num_download, title))

            # get abstract page url
            url2 = this_paper.a.get('href')
            abs_url = urllib.parse.urljoin(init_url, url2)
            for i in range(3):  # try 3 times
                try:
                    req = urllib.request.Request(url=abs_url, headers=headers)
                    abs_content = urllib.request.urlopen(req, timeout=10).read()
                    soup_temp = BeautifulSoup(abs_content, 'html.parser')
                    # abstract = soup_temp.find('p', {'class': 'abstract'}).text.strip()
                    # paper_dict[title] = abstract
                    all_a = soup_temp.findAll('a')
                    for a in all_a:
                        # print(a.text[:-2])
                        # print(a.text[:-2].strip().lower())
                        if 'paper' == a.text[:-2].strip().lower():
                            paper_dict['main link'] = urllib.parse.urljoin(abs_url, a.get('href'))
                        elif 'supplemental' == a.text[:-2].strip().lower():
                            paper_dict['supplemental link'] = urllib.parse.urljoin(abs_url, a.get('href'))
                            break
                    break
                except Exception as e:
                    if i == 2:
                        print('Error: ' + title + ' - ' + str(e))
                        if paper_dict['main link'] == '':
                            paper_dict['main link'] = 'error'
                        if paper_dict['supplemental link'] == '':
                            paper_dict['supplemental link'] = 'error'
            writer.writerow(paper_dict)
            time.sleep(1)
    return num_download


# def save_csv(year):
#     """
#     write nips papers' and supplemental material's urls in one csv file
#     :param year: int
#     :return: num_dowload: int, the total number of papers.
#     """
#     with open(f'..\\csv\\NIPS_{year}.csv', 'w', newline='') as csvfile:
#         fieldnames = ['title', 'main link', 'supplemental link']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()
#
#         init_url = f'http://papers.nips.cc/book/advances-in-neural-information-processing-systems-{year - 1987}-{year}'
#         paper_website = 'http://papers.nips.cc'
#         if os.path.exists(f'..\\urls\\init_url_nips_{year}.dat'):
#             with open(f'..\\urls\\init_url_nips_{year}.dat', 'rb') as f:
#                 content = pickle.load(f)
#         else:
#             content = urlopen(init_url).read()
#             with open(f'..\\urls\\init_url_nips_{year}.dat', 'wb') as f:
#                 pickle.dump(content, f)
#         soup = BeautifulSoup(content, 'html.parser')
#         temp_soup = soup.find_all('ul')[1]  # after the book section
#         paper_list = temp_soup.find_all('li')
#         # num_download = 5 # number of papers to download
#         num_download = len(paper_list)
#         paper_list_bar = tqdm(zip(paper_list, range(num_download)))
#         for paper in tqdm(zip(paper_list, range(num_download))):
#             paper_dict = {'title': '',
#                           'main link': '',
#                           'supplemental link': ''}
#             # get title
#             # print('\n')
#             this_paper = paper[0]
#             title = slugify(this_paper.a.text)
#             paper_dict['title'] = title
#             # print('Downloading paper {}/{}: {}'.format(paper[1] + 1, num_download, title))
#             paper_list_bar.set_description('Tracing paper {}/{}: {}'.format(paper[1] + 1, num_download, title))
#
#             # get abstract page url
#             url2 = this_paper.a.get('href')
#             for i in range(3):  # try 3 times
#                 try:
#                     abs_content = urlopen(paper_website + url2, timeout=50).read()
#                     soup_temp = BeautifulSoup(abs_content, 'html.parser')
#                     # abstract = soup_temp.find('p', {'class': 'abstract'}).text.strip()
#                     # paper_dict[title] = abstract
#                     all_a = soup_temp.findAll('a')
#                     for a in all_a[4:]:
#                         if '[PDF]' == a.text:
#                             paper_dict['main link'] = paper_website + a.get('href')
#                         elif '[Supplemental]' == a.text:
#                             paper_dict['supplemental link'] = paper_website + a.get('href')
#                             break
#                     break
#                 except Exception as e:
#                     if i == 2:
#                         print('Error: ' + title + ' - ' + str(e))
#                         if paper_dict['main link'] == '':
#                             paper_dict['main link'] = 'error'
#                         if paper_dict['supplemental link'] == '':
#                             paper_dict['supplemental link'] = 'error'
#             writer.writerow(paper_dict)
#             time.sleep(1)
#     return num_download


def download_from_csv(
        year, save_dir, is_download_mainpaper=True, is_download_supplement=True,
        time_step_in_seconds=5, total_paper_number=None, downloader='IDM'):
    """
    download all NIPS paper and supplement files given year, restore in save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, NIPS year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_mainpaper: boot, True for downloading main papers
    :param is_download_supplement: bool, True for downloading supplemental material
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :param total_paper_number: int, the total number of papers that is going to download
    :param downloader: str, the downloader to download, could be 'IDM' or 'Thunder', default to 'IDM'
    :return: True
    """
    postfix = f'NIPS_{year}'
    csv_file_path = f'..\\csv\\NIPS_{year}.csv'
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
#             this_paper_supp_path_no_ext = os.path.join(supp_dir, f'{title}_{postfix}_supp.')
#
#             if '' != this_paper['supplemental link']:
#                 supp_ori_name = this_paper['supplemental link'].split('/')[-1]
#                 supp_type = supp_ori_name.split('.')[-1]
#                 if os.path.exists(os.path.join(supp_dir, supp_ori_name)) and not os.path.exists(
#                         this_paper_supp_path_no_ext + supp_type):
#                     os.rename(
#                         os.path.join(supp_dir, supp_ori_name),
#                         this_paper_supp_path_no_ext + supp_type
#                     )
#                 pbar.set_description(f'Renaming paper: {title}...')


if __name__ == '__main__':
    year = 2022
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
        base_url='https://openreview.net/group?id=NeurIPS.cc/2022/Conference',
        time_step_in_seconds=10,
        downloader='IDM')
    # move_main_and_supplement_2_one_directory(
    #     main_path=rf'F:\workspace\python3_ws\paper_downloader-master\NIPS_{year}\main_paper',
    #     supplement_path=rf'F:\workspace\python3_ws\paper_downloader-master\NIPS_{year}\supplement',
    #     supp_pdf_save_path=rf'F:\workspace\python3_ws\paper_downloader-master\NIPS_{year}\supplement_pdf'
    # )
