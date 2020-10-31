"""paper_download_COLT_IDM.py"""

from urllib.request import urlopen
import time
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


def download_paper_IDM(year, save_dir):
    """
    download all COLT papers given year, restore in save_dir
    :param year: int, COLT year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :return: True
    """
    COLT_year_dict = {2020: 125,
                      2019: 99,
                      2018: 75,
                      2017: 65,
                      2016: 49,
                      2015: 40,
                      2014: 35,
                      2013: 30,
                      2012: 23,
                      2011: 19
                      }
    if year >= 2011 and year <= 2020:
        init_url = f'http://proceedings.mlr.press/v{COLT_year_dict[year]}/'
    else:
        raise ValueError('''the given year's url is unknown !''')
    # init_url = f'http://papers.nips.cc/book/advances-in-neural-information-processing-systems-{year-1987}-{year}'
    os.makedirs(save_dir, exist_ok=True)
    # use IDM to download everything
    idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'''  # should replace by the local IDM path
    basic_command = [idm_path, '/d', 'xxxx', '/p', os.getcwd(), '/f', 'xxxx', '/n']  # silent /n
    # create current dict
    title_list = []
    # paper_dict = dict()

    postfix = f'COLT_{year}'
    if os.path.exists(f'..\\urls\\init_url_COLT_{year}.dat'):
        with open(f'..\\urls\\init_url_COLT_{year}.dat', 'rb') as f:
            content = pickle.load(f)
    else:
        content = urlopen(init_url).read()
        with open(f'..\\urls\\init_url_COLT_{year}.dat', 'wb') as f:
            pickle.dump(content, f)
    soup = BeautifulSoup(content, 'html.parser')
    paper_list = soup.find_all('div', {'class': 'paper'})
    error_log = []
    # num_download = 5 # number of papers to download
    num_download = len(paper_list)
    for paper in tqdm(zip(paper_list, range(num_download))):
        # get title
        print('\n')
        this_paper = paper[0]
        title = slugify(this_paper.find_all('p', {'class': 'title'})[0].text)
        try:
            print('Downloading paper {}/{}: {}'.format(paper[1]+1, num_download, title))
        except:
            print(title.encode('utf8'))
        title_list.append(title)

        this_paper_main_path = os.path.join(save_dir, f'{title}_{postfix}.pdf')
        if os.path.exists(this_paper_main_path):
            continue

        # get abstract page url
        links = this_paper.find_all('p', {'class': 'links'})[0].find_all('a')
        main_link = None
        for link in links:
            if 'Download PDF' == link.text:
                main_link = link.get('href')

        # try 1 time
        # error_flag = False
        for d_iter in range(1):
            try:
                # download paper with IDM
                if not os.path.exists(this_paper_main_path) and main_link is not None:
                    basic_command[2] = main_link
                    basic_command[6] = this_paper_main_path
                    p = subprocess.Popen(' '.join(basic_command))
                    p.wait()
                    time.sleep(5)
                    # while True:
                    #     if os.path.exists(this_paper_main_path):
                    #         break
            except Exception as e:
                # error_flag = True
                print('Error: ' + title + ' - ' + str(e))
                error_log.append((title, main_link, 'main paper download error', str(e)))

    # store the results
    # 1. store in the pickle file
    # with open(f'{postfix}_pre.dat', 'wb') as f:
    #     pickle.dump(paper_dict, f)

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
    download_paper_IDM(year, f'..\\COLT_{year}')
    pass