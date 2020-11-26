"""paper_download_JMLR_IDM.py"""

import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pickle
import os
from tqdm import tqdm
from slugify import slugify
import lib.IDM as IDM


def download_paper_IDM(volumn, save_dir, time_step_in_seconds=5):
    """
    download all JMLR paper and supplement files given volumn, restore in save_dir/main_paper and save_dir/supplement
    respectively
    :param volumn: int, JMLR volumn, such as 2019
    :param save_dir: str, paper and supplement material's save path
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :return: True
    """
    init_url = f'http://jmlr.org/papers/v{volumn}/'

    # create current dict
    title_list = []
    # paper_dict = dict()

    headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
    postfix = f'JMLR_v{volumn}'
    if os.path.exists(f'..\\urls\\init_url_JMLR_v{volumn}.dat'):
        with open(f'..\\urls\\init_url_JMLR_v{volumn}.dat', 'rb') as f:
            content = pickle.load(f)
    else:
        req = urllib.request.Request(url=init_url, headers=headers)
        content = urllib.request.urlopen(req, timeout=10).read()
        # content = open(f'..\\JMLR_{volumn}.html', 'rb').read()
        with open(f'..\\urls\\init_url_JMLR_v{volumn}.dat', 'wb') as f:
            pickle.dump(content, f)
    # soup = BeautifulSoup(content, 'html.parser')
    soup = BeautifulSoup(content, 'html5lib')
    # soup = BeautifulSoup(open(r'..\JMLR_2011.html', 'rb'), 'html.parser')
    error_log = []
    os.makedirs(save_dir, exist_ok=True)
    if volumn <= 4:
        paper_list = soup.find('div', {'id': 'content'}).find_all('tr')
    else:
        paper_list = soup.find('div', {'id': 'content'}).find_all('dl')
    # num_download = 5 # number of papers to download
    num_download = len(paper_list)
    for paper in tqdm(zip(paper_list, range(num_download))):
        # get title
        print('\n')
        this_paper = paper[0]
        title = slugify(this_paper.find('dt').text)
        try:
            print('Downloading paper {}/{}: {}'.format(paper[1]+1, num_download, title))
        except:
            print(title.encode('utf8'))
        title_list.append(title)

        this_paper_main_path = os.path.join(save_dir, f'{title}_{postfix}.pdf'.replace(' ', '_'))
        if os.path.exists(this_paper_main_path):
            continue

        # get abstract page url
        links = this_paper.find_all('a')
        main_link = None
        for link in links:
            if '[pdf]' == link.text or 'pdf' == link.text:
                main_link = urllib.parse.urljoin('http://jmlr.org', link.get('href'))
                break

        # try 1 time
        # error_flag = False
        for d_iter in range(1):
            try:
                # download paper with IDM
                if not os.path.exists(this_paper_main_path) and main_link is not None:
                    IDM.download(
                        urls=main_link,
                        save_path=this_paper_main_path,
                        time_sleep_in_seconds=time_step_in_seconds
                    )
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
    volumn = 21
    download_paper_IDM(volumn, f'..\\JMLR_v{volumn}', time_step_in_seconds=1)
    pass
