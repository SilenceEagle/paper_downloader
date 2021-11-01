"""
csv_process.py
20210617
"""


import os
from tqdm import tqdm
from slugify import slugify
import csv
from lib.downloader import Downloader


def download_from_csv(
        postfix, save_dir, csv_file_path, is_download_main_paper=True,
        is_download_supplement=True, time_step_in_seconds=5, total_paper_number=None,
        downloader='IDM'):
    """
    download paper and supplement files and save them to save_dir/main_paper and save_dir/supplement
        respectively
    :param postfix: str, postfix that will be added at the end of papers' title
    :param save_dir: str, paper and supplement material's save path
    :param csv_file_path: str, the full path to csv file
    :param is_download_main_paper: bool, True for downloading main paper
    :param is_download_supplement: bool, True for downloading supplemental material
    :param time_step_in_seconds: int, the interval time between two downloading request in seconds
    :param total_paper_number: int, the total number of papers that is going to download
    :param downloader: str, the downloader to download, could be 'IDM' or 'Thunder', default to 'IDM'.
    :return: True
    """
    downloader = Downloader(downloader=downloader)
    if not os.path.exists(csv_file_path):
        raise ValueError(f'ERROR: file not found in {csv_file_path}!!!')

    main_save_path = os.path.join(save_dir, 'main_paper')
    if is_download_main_paper:
        os.makedirs(main_save_path, exist_ok=True)
    if is_download_supplement:
        supplement_save_path = os.path.join(save_dir, 'supplement')
        os.makedirs(supplement_save_path, exist_ok=True)

    error_log = []
    with open(csv_file_path, newline='') as csvfile:
        myreader = csv.DictReader(csvfile, delimiter=',')
        pbar = tqdm(myreader)
        i = 0
        for this_paper in pbar:
            is_grouped = ('group' in this_paper)
            i += 1
            # get title
            if is_grouped:
                group = slugify(this_paper['group'])
            title = slugify(this_paper['title'])
            if total_paper_number is not None:
                pbar.set_description(f'Downloading paper {i}/{total_paper_number}')
            else:
                pbar.set_description(f'Downloading paper {i}')
            this_paper_main_path = os.path.join(main_save_path, f'{title}_{postfix}.pdf')
            if is_grouped:
                this_paper_main_path = os.path.join(main_save_path, group, f'{title}_{postfix}.pdf')
            if is_download_supplement:
                this_paper_supp_path_no_ext = os.path.join(supplement_save_path, f'{title}_{postfix}_supp.')
                if is_grouped:
                    this_paper_supp_path_no_ext = os.path.join(supplement_save_path, group, f'{title}_{postfix}_supp.')
                if '' != this_paper['supplemental link'] and os.path.exists(this_paper_main_path) and \
                        (os.path.exists(this_paper_supp_path_no_ext + 'zip') or os.path.exists(
                            this_paper_supp_path_no_ext + 'pdf')):
                    continue
                elif '' == this_paper['supplemental link'] and os.path.exists(this_paper_main_path):
                    continue
            elif os.path.exists(this_paper_main_path):
                    continue
            if 'error' == this_paper['main link']:
                error_log.append((title, 'no MAIN link'))
            elif '' != this_paper['main link']:
                if is_grouped:
                    if is_download_main_paper:
                        os.makedirs(os.path.join(main_save_path, group), exist_ok=True)
                    if is_download_supplement:
                        os.makedirs(os.path.join(supplement_save_path, group), exist_ok=True)
                if is_download_main_paper:
                    try:
                        # download paper with IDM
                        if not os.path.exists(this_paper_main_path):
                            downloader.download(
                                urls=this_paper['main link'].replace(' ', '%20'),
                                save_path=os.path.join(os.getcwd(), this_paper_main_path),
                                time_sleep_in_seconds=time_step_in_seconds
                            )
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
                                downloader.download(
                                    urls=this_paper['supplemental link'],
                                    save_path=os.path.join(os.getcwd(), this_paper_supp_path_no_ext+supp_type),
                                    time_sleep_in_seconds=time_step_in_seconds
                                )
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

    return True