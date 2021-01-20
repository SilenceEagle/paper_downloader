"""paper_download_AISTATS_IDM.py"""

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
import lib.IDM as IDM
import lib.thunder as Thunder


def download_paper_and_sup_IDM(year, save_dir, is_download_supplement=True, time_step_in_seconds=10, downloader='IDM'):
    """
    download all AISTATS paper and supplement files given year, restore in save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, AISTATS year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental material
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :param downloader: str, the downloader to download, could be 'IDM' or 'Thunder', default to 'IDM'
    :return: True
    """
    AISTATS_year_dict = {2020: 108,
                         2019: 89,
                         2018: 84,
                         2017: 54,
                         2016: 51,
                         2015: 38,
                         2014: 33,
                         2013: 31,
                         2012: 22,
                         2011: 15,
                         2010: 9,
                         2009: 5,
                         2007: 2
                         }
    AISTATS_year_dict_R = {
        1999: 1
    }
    if year in AISTATS_year_dict.keys():
        init_url = f'http://proceedings.mlr.press/v{AISTATS_year_dict[year]}/'
    elif year in AISTATS_year_dict_R.keys():
        init_url = f'http://proceedings.mlr.press/r{AISTATS_year_dict_R[year]}/'
    else:
        raise ValueError('''the given year's url is unknown !''')
    # init_url = f'http://papers.nips.cc/book/advances-in-neural-information-processing-systems-{year-1987}-{year}'
    if is_download_supplement:
        main_save_path = os.path.join(save_dir, 'main_paper')
        supplement_save_path = os.path.join(save_dir, 'supplement')
        os.makedirs(main_save_path, exist_ok=True)
        os.makedirs(supplement_save_path, exist_ok=True)
    else:
        main_save_path = save_dir
        os.makedirs(main_save_path, exist_ok=True)
    # create current dict
    title_list = []
    # paper_dict = dict()

    postfix = f'AISTATS_{year}'
    if os.path.exists(f'..\\urls\\init_url_AISTATS_{year}.dat'):
        with open(f'..\\urls\\init_url_AISTATS_{year}.dat', 'rb') as f:
            content = pickle.load(f)
    else:
        content = urlopen(init_url).read()
        with open(f'..\\urls\\init_url_AISTATS_{year}.dat', 'wb') as f:
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

        this_paper_main_path = os.path.join(main_save_path, f'{title}_{postfix}.pdf'.replace(' ', '_'))
        if is_download_supplement:
            this_paper_supp_path = os.path.join(supplement_save_path, f'{title}_{postfix}_supp.pdf')
            this_paper_supp_path_no_ext = os.path.join(supplement_save_path, f'{title}_{postfix}_supp.')

            if os.path.exists(this_paper_main_path) and os.path.exists(this_paper_supp_path):
                continue
        else:
            if os.path.exists(this_paper_main_path):
                continue

        # get abstract page url
        links = this_paper.find_all('p', {'class': 'links'})[0].find_all('a')
        supp_link = None
        main_link = None
        for link in links:
            if 'Download PDF' == link.text or 'pdf' == link.text:
                main_link = link.get('href')
            elif is_download_supplement and ('Supplementary PDF' == link.text or 'Supplementary Material' == link.text or \
                    'supplementary' == link.text):
                supp_link = link.get('href')
                if supp_link[-3:] != 'pdf':
                    this_paper_supp_path = this_paper_supp_path_no_ext + supp_link[-3:]


        # try 1 time
        # error_flag = False
        for d_iter in range(1):
            try:
                # download paper with IDM
                if not os.path.exists(this_paper_main_path) and main_link is not None:
                    if 'IDM' == downloader:
                        IDM.download(
                            urls=main_link,
                            save_path=this_paper_main_path,
                            time_sleep_in_seconds=time_step_in_seconds
                        )
                    elif 'Thunder' == downloader:
                        Thunder.download(
                            urls=main_link,
                            save_path=this_paper_main_path,
                            time_sleep_in_seconds=time_step_in_seconds
                        )
                    else:
                        raise ValueError(
                            f'''ERROR: Unsupported downloader: {downloader}, we currently only support'''
                            f''' "IDM" or "Thunder" ''')
                    # while True:
                    #     if os.path.exists(this_paper_main_path):
                    #         break
            except Exception as e:
                # error_flag = True
                print('Error: ' + title + ' - ' + str(e))
                error_log.append((title, main_link, 'main paper download error', str(e)))
            # download supp
            if is_download_supplement:
                # check whether the supp can be downloaded
                if not os.path.exists(this_paper_supp_path) and supp_link is not None:
                    try:
                        if 'IDM' == downloader:
                            IDM.download(
                                urls=supp_link,
                                save_path=this_paper_supp_path,
                                time_sleep_in_seconds=time_step_in_seconds
                            )
                        elif 'Thunder' == downloader:
                            Thunder.download(
                                urls=supp_link,
                                save_path=this_paper_supp_path,
                                time_sleep_in_seconds=time_step_in_seconds
                            )
                        else:
                            raise ValueError(
                                f'''ERROR: Unsupported downloader: {downloader}, we currently only support'''
                                f''' "IDM" or "Thunder" ''')
                        # while True:
                        #     if os.path.exists(this_paper_supp_path_no_ext + supp_type):
                        #         break
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append((title, supp_link, 'supplement download error', str(e)))

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
    year = 1999
    download_paper_and_sup_IDM(
        year,
        rf'F:\AISTATS_{year}',
        is_download_supplement=False,
        time_step_in_seconds=5,
        downloader='IDM'
    )
    pass
