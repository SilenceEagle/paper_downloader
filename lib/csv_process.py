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
        is_download_bib=True, is_download_supplement=True,
        time_step_in_seconds=5, total_paper_number=None,
        downloader='IDM', is_random_step=True, proxy_ip_port=None,
        max_length_filename=128
):
    """
    download paper, bibtex and supplement files and save them to
        save_dir/main_paper and save_dir/supplement respectively
    :param postfix: str, postfix that will be added at the end of papers' title
    :param save_dir: str, paper and supplement material's save path
    :param csv_file_path: str, the full path to csv file
    :param is_download_main_paper: bool, True for downloading main paper
    :param is_download_supplement: bool, True for downloading supplemental
        material
    :param time_step_in_seconds: int, the interval time between two downloading
        request in seconds
    :param total_paper_number: int, the total number of papers that is going to
        download
    :param downloader: str, the downloader to download, could be 'IDM' or None,
        default to 'IDM'.
    :param is_random_step: bool, whether random sample the time step between two
        adjacent download requests. If True, the time step will be sampled
        from Uniform(0.5t, 1.5t), where t is the given time_step_in_seconds.
        Default: True.
    :param proxy_ip_port: str or None, proxy server ip address with or without
        protocol prefix, eg: "127.0.0.1:7890", "http://127.0.0.1:7890".
        Default: None
    :param max_length_filename: int or None, max filen name length. All the
            files whose name length is not less than this will be renamed
            before saving, the others will stay unchanged. None means
            no limitation. Default: 128.
    :return: True
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    downloader = Downloader(
        downloader=downloader, is_random_step=is_random_step,
        proxy_ip_port=proxy_ip_port)
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
        pbar = tqdm(myreader, total=total_paper_number)
        i = 0
        for this_paper in pbar:
            is_download_bib &= ('bib' in this_paper)
            is_grouped = ('group' in this_paper)
            i += 1
            # get title
            if is_grouped:
                group = slugify(this_paper['group'])
            title = slugify(this_paper['title'])
            title_main_pdf = short_name(
                name=f'{title}_{postfix}.pdf',
                max_length=max_length_filename
            )
            if total_paper_number is not None:
                pbar.set_description(
                    f'Downloading {postfix} paper {i} /{total_paper_number}')
            else:
                pbar.set_description(f'Downloading {postfix} paper {i}')
            this_paper_main_path = os.path.join(
                main_save_path, title_main_pdf)
            if is_grouped:
                this_paper_main_path = os.path.join(
                    main_save_path, group, title_main_pdf)
            if is_download_supplement:
                this_paper_supp_title_no_ext = short_name(
                    name=f'{title}_{postfix}_supp.',
                    max_length=max_length_filename-3  # zip or pdf, so 3
                )
                this_paper_supp_path_no_ext = os.path.join(
                    supplement_save_path, this_paper_supp_title_no_ext)
                if is_grouped:
                    this_paper_supp_path_no_ext = os.path.join(
                        supplement_save_path, group,
                        this_paper_supp_title_no_ext
                    )
                if '' != this_paper['supplemental link'] and os.path.exists(
                        this_paper_main_path) and \
                        (os.path.exists(
                            this_paper_supp_path_no_ext + 'zip') or
                         os.path.exists(
                            this_paper_supp_path_no_ext + 'pdf')):
                    continue
                elif '' == this_paper['supplemental link'] and \
                        os.path.exists(this_paper_main_path):
                    continue
            elif os.path.exists(this_paper_main_path):
                continue
            if 'error' == this_paper['main link']:
                error_log.append((title, 'no MAIN link'))
            elif '' != this_paper['main link']:
                if is_grouped:
                    if is_download_main_paper:
                        os.makedirs(os.path.join(main_save_path, group),
                                    exist_ok=True)
                    if is_download_supplement:
                        os.makedirs(os.path.join(supplement_save_path, group),
                                    exist_ok=True)
                if is_download_main_paper:
                    try:
                        # download paper with IDM
                        if not os.path.exists(this_paper_main_path):
                            downloader.download(
                                urls=this_paper['main link'].replace(
                                    ' ', '%20'),
                                save_path=os.path.join(
                                    os.getcwd(), this_paper_main_path),
                                time_sleep_in_seconds=time_step_in_seconds
                            )
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append((title, this_paper['main link'],
                                          'main paper download error', str(e)))
                # download supp
                if is_download_supplement:
                    # check whether the supp can be downloaded
                    if not (os.path.exists(
                            this_paper_supp_path_no_ext + 'zip') or
                            os.path.exists(
                                this_paper_supp_path_no_ext + 'pdf')):
                        if 'error' == this_paper['supplemental link']:
                            error_log.append((title, 'no SUPPLEMENTAL link'))
                        elif '' != this_paper['supplemental link']:
                            supp_type = \
                            this_paper['supplemental link'].split('.')[-1]
                            try:
                                downloader.download(
                                    urls=this_paper['supplemental link'],
                                    save_path=os.path.join(
                                        os.getcwd(),
                                        this_paper_supp_path_no_ext + supp_type),
                                    time_sleep_in_seconds=time_step_in_seconds
                                )
                            except Exception as e:
                                # error_flag = True
                                print('Error: ' + title + ' - ' + str(e))
                                error_log.append((title, this_paper[
                                    'supplemental link'],
                                                  'supplement download error',
                                                  str(e)))
                # download bibtex file
                if is_download_bib:
                    bib_path = this_paper_main_path[:-3] + 'bib'
                    if not os.path.exists(bib_path):
                        if 'error' == this_paper['bib']:
                            error_log.append((title, 'no bibtex link'))
                        elif '' != this_paper['bib']:
                            try:
                                downloader.download(
                                    urls=this_paper['bib'],
                                    save_path=os.path.join(os.getcwd(),
                                                           bib_path),
                                    time_sleep_in_seconds=time_step_in_seconds
                                )
                            except Exception as e:
                                # error_flag = True
                                print('Error: ' + title + ' - ' + str(e))
                                error_log.append((title, this_paper['bib'],
                                                  'bibtex download error',
                                                  str(e)))

        # 2. write error log
        print('write error log')
        log_file_pathname = os.path.join(
            project_root_folder, 'log', 'download_err_log.txt'
        )
        with open(log_file_pathname, 'w') as f:
            for log in tqdm(error_log):
                for e in log:
                    if e is not None:
                        f.write(e)
                    else:
                        f.write('None')
                    f.write('\n')

                f.write('\n')

    return True


def short_name(name, max_length, verbose=False):
    """
    rename to shorter name
    Args:
        name (str): original name
        max_length (int): max filen name length. All the
            files whose name length is not less than this will be renamed
            before saving, the others will stay unchanged. None means
            no limitation.
        verbose (bool): whether to print debug information. Default: False.
    Returns:
        new_name (str): short name.
    """
    if len(name) < max_length:
        new_name = name
    else:
        # rename
        try:
            [title, postfix] = name.split('_', 1)  # only split to 2 parts
            new_title = title[:max_length - len(postfix) - 2]
            new_name = f'{new_title}_{postfix}'
            if verbose:
                print(f'\nrenaming {name} \n\t-> {new_name}')
        except ValueError:
            # ValueError: not enough values to unpack (expected 2, got 1)
            if verbose:
                print(f'\nWARNING!!!:\n\tunable to parse postfix from {name}')
                print('\tSo, it will be just rename to short name')
            ext = os.path.splitext(name)[1]
            new_title = name[:max_length - len(ext) - 1]
            new_name = f'{new_title}{ext}'
            if verbose:
                print(f'\nrenaming {name} \n\t-> {new_name}')
    return new_name
