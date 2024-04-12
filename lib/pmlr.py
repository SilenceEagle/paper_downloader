"""
pmlr.py
20210618
"""
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
from slugify import slugify
from lib.downloader import Downloader
from .my_request import urlopen_with_retry


def download_paper_given_volume(
        volume, save_dir, postfix, is_download_supplement=True,
        time_step_in_seconds=5, downloader='IDM', is_random_step=True):
    """
    download main and supplement papers from PMLR.
    :param volume: str, such as 'v1', 'r1'
    :param save_dir: str, paper and supplement material's save path
    :param postfix: str, the postfix will be appended to the end of papers' titles
    :param is_download_supplement: bool, True for downloading supplemental material
    :param time_step_in_seconds: int, the interval time between two downloading
        requests in seconds
    :param downloader: str, the downloader to download, could be 'IDM' or None,
        Default: 'IDM'
    :param is_random_step: bool, whether random sample the time step between two
        adjacent download requests. If True, the time step will be sampled
        from Uniform(0.5t, 1.5t), where t is the given time_step_in_seconds.
        Default: True.
    :return: True
    """
    downloader = Downloader(
        downloader=downloader, is_random_step=is_random_step)
    init_url = f'http://proceedings.mlr.press/{volume}/'

    if is_download_supplement:
        main_save_path = os.path.join(save_dir, 'main_paper')
        supplement_save_path = os.path.join(save_dir, 'supplement')
        os.makedirs(main_save_path, exist_ok=True)
        os.makedirs(supplement_save_path, exist_ok=True)
    else:
        main_save_path = save_dir
        os.makedirs(main_save_path, exist_ok=True)
    headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
            'Gecko/20100101 Firefox/23.0'}
    content = urlopen_with_retry(url=init_url, headers=headers)
    soup = BeautifulSoup(content, 'html.parser')
    paper_list = soup.find_all('div', {'class': 'paper'})
    error_log = []
    title_list = []
    num_download = len(paper_list)
    pbar = tqdm(zip(paper_list, range(num_download)), total=num_download)
    for paper in pbar:
        # get title
        this_paper = paper[0]
        title = slugify(this_paper.find_all('p', {'class': 'title'})[0].text)
        try:
            pbar.set_description(
                f'Downloading {postfix} paper {paper[1] + 1}/{num_download}:'
                f' {title}')
        except:
            pbar.set_description(
                f'''Downloading {postfix} paper {paper[1] + 1}/{num_download}: '''
                f'''{title.encode('utf8')}''')
        title_list.append(title)

        this_paper_main_path = os.path.join(main_save_path,
                                            f'{title}_{postfix}.pdf')
        if is_download_supplement:
            this_paper_supp_path = os.path.join(
                supplement_save_path, f'{title}_{postfix}_supp.pdf')
            this_paper_supp_path_no_ext = os.path.join(
                supplement_save_path, f'{title}_{postfix}_supp.')

            if os.path.exists(this_paper_main_path) and os.path.exists(
                    this_paper_supp_path):
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
            elif is_download_supplement and \
                    ('Supplementary PDF' == link.text or
                     'Supplementary Material' == link.text or
                     'supplementary' == link.text or
                     'Supplementary ZIP' == link.text or
                     'Other Files' == link.text):
                supp_link = link.get('href')
                if supp_link[-3:] != 'pdf':
                    this_paper_supp_path = this_paper_supp_path_no_ext + \
                                           supp_link[-3:]

        # try 1 time
        # error_flag = False
        for d_iter in range(1):
            try:
                # download paper with IDM
                if not os.path.exists(
                        this_paper_main_path) and main_link is not None:
                    downloader.download(
                        urls=main_link,
                        save_path=this_paper_main_path,
                        time_sleep_in_seconds=time_step_in_seconds
                    )
            except Exception as e:
                # error_flag = True
                print('Error: ' + title + ' - ' + str(e))
                error_log.append(
                    (title, main_link, 'main paper download error', str(e)))
            # download supp
            if is_download_supplement:
                # check whether the supp can be downloaded
                if not os.path.exists(
                        this_paper_supp_path) and supp_link is not None:
                    try:
                        downloader.download(
                            urls=supp_link,
                            save_path=this_paper_supp_path,
                            time_sleep_in_seconds=time_step_in_seconds
                        )
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append((title, supp_link,
                                          'supplement download error', str(e)))

    # write error log
    print('writing error log...')
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'download_err_log.txt')
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


if __name__ == '__main__':
    download_paper_given_volume(
        volume=150,
        save_dir=r'D:\The_KDD21_Workshop_on_Causal_Discovery',
        postfix=f'',
        is_download_supplement=False,
        time_step_in_seconds=5,
        downloader='IDM'
    )
