"""paper_downloader_ICLR.py"""

from tqdm import tqdm
import os
# https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename
from slugify import slugify
from bs4 import BeautifulSoup
import pickle
from urllib.request import urlopen
import urllib
import sys

root_folder = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
from lib.downloader import Downloader
from lib.openreview import download_iclr_papers_given_url_and_group_id
from lib.arxiv import get_pdf_link_from_arxiv


def download_iclr_oral_papers(save_dir, year, base_url=None,
                              time_step_in_seconds=10, downloader='IDM',
                              start_page=1, proxy_ip_port=None):
    """
    Download iclr oral papers for year 2017 ~ 2022, 2024~2025.
    :param save_dir: str, paper save path
    :param year: int, iclr year, current only support year >= 2018
    :param base_url: str, paper website url
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds.
    :param downloader: str, the downloader to download, could be 'IDM' or
        None, default to 'IDM'.
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Currently, this parameter is only used in year 2024.
        Default: 1.
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Default: None.
    :type proxy_ip_port: str | None
    :return:
    """
    group_id_dict = {
        2025: "tab-accept-oral",
        2024: "tab-accept-oral",
        2022: "oral-submissions",
        2021: "oral-presentations",
        2020: "oral-presentations",
        2019: "oral-presentations",
        2018: "accepted-oral-papers",
        2017: "oral-presentations",
        2013: "conferenceoral-iclr2013-conference"
    }
    
    if base_url is None:
        if year in group_id_dict:
            base_url = 'https://openreview.net/group?id=ICLR.cc/' \
                f'{year}/Conference#{group_id_dict[year]}'
        else:
            raise ValueError('the website url is not given for this year!')
        
    print(f'Downloading ICLR-{year} oral papers...')
    group_id = group_id_dict[year].replace('tab-', '')
    download_iclr_papers_given_url_and_group_id(
        save_dir=save_dir,
        year=year,
        base_url=base_url,
        group_id=group_id,
        start_page=start_page,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader,
        proxy_ip_port=proxy_ip_port,
        is_have_pages=(year > 2021)
    )


def download_iclr_conditional_oral_papers(save_dir, year, base_url=None,
                              time_step_in_seconds=10, downloader='IDM',
                              start_page=1, proxy_ip_port=None):
    """
    Download iclr conditional oral papers for year 2025.
    :param save_dir: str, paper save path
    :param year: int, iclr year, current only support year >= 2018
    :param base_url: str, paper website url
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds.
    :param downloader: str, the downloader to download, could be 'IDM' or
        None, default to 'IDM'.
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Currently, this parameter is only used in year 2024.
        Default: 1.
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Default: None.
    :type proxy_ip_port: str | None
    :return:
    """
    group_id_dict = {
        2025: "tab-accept-conditional-oral"
    }
    no_pages_year = [2025]
    if base_url is None:
        if year in group_id_dict:
            base_url = 'https://openreview.net/group?id=ICLR.cc/' \
                f'{year}/Conference#{group_id_dict[year]}'
        else:
            raise ValueError('the website url is not given for this year!')
    print(f'Downloading ICLR-{year} conditional oral papers...')
    group_id = group_id_dict[year].replace('tab-', '')
    download_iclr_papers_given_url_and_group_id(
        save_dir=save_dir,
        year=year,
        base_url=base_url,
        group_id=group_id,
        start_page=start_page,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader,
        proxy_ip_port=proxy_ip_port,
        is_have_pages=(year not in no_pages_year)
    )


def download_iclr_top5_papers(save_dir, year, base_url=None, start_page=1,
                              time_step_in_seconds=10, downloader='IDM',
                              proxy_ip_port=None):
    """
    Download iclr notable-top-5% papers for year 2023.
    :param save_dir: str, paper save path
    :param year: int, iclr year
    :type year: int
    :param base_url: str, paper website url
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Default: 1
    :param time_step_in_seconds: int, the interval time between two downlaod
        request in seconds. Default: 10.
    :type time_step_in_seconds: int
    :param downloader: str, the downloader to download, could be 'IDM' or
        None. Default: 'IDM'.
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Default: None.
    :type proxy_ip_port: str | None
    :return:
    """
    if base_url is None:
        if year == 2023:
            base_url = "https://openreview.net/group?id=ICLR.cc/" \
                       "2023/Conference#notable-top-5-"
        else:
            raise ValueError('the website url is not given for this year!')
    print(f'Downloading ICLR-{year} top5 papers...')
    group_id = "notable-top-5-"
    return download_iclr_papers_given_url_and_group_id(
        save_dir=save_dir,
        year=year,
        base_url=base_url,
        group_id=group_id,
        start_page=start_page,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader,
        proxy_ip_port=proxy_ip_port
    )


def download_iclr_poster_papers(save_dir, year, base_url=None, start_page=1,
                                time_step_in_seconds=10, downloader='IDM',
                                proxy_ip_port=None):
    """
    Download iclr poster papers from year 2013, 2017 ~ 2024.
    :param save_dir: str, paper save path
    :param year: int, iclr year, current only support year
    :param base_url: str, paper website url
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Default: 1
    :param time_step_in_seconds: int, the interval time between two downlaod
        request in seconds
    :param downloader: str, the downloader to download, could be 'IDM' or
        None. Default: 'IDM'
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Default: None.
    :type proxy_ip_port: str | None
    :return:
    """
    group_id_dict = {
        2025: "tab-accept-poster",
        2024: "tab-accept-poster",
        2023: "poster",
        2022: "poster-submissions",
        2021: "poster-presentations",
        2020: "poster-presentations",
        2019: "poster-presentations",
        2018: "accepted-poster-papers",
        2017: "poster-presentations",
        2013: "conferenceposter-iclr2013-conference"
    }
    if base_url is None:
        if year in group_id_dict:
            base_url = 'https://openreview.net/group?id=ICLR.cc/' \
                f'{year}/Conference#{group_id_dict[year]}'
        else:
            raise ValueError('the website url is not given for this year!')
    print(f'Downloading ICLR-{year} poster papers...')
    no_pages_year = [2013, 2018, 2019, 2020, 2021]
    download_iclr_papers_given_url_and_group_id(
        save_dir=save_dir,
        year=year,
        base_url=base_url,
        group_id=group_id_dict[year].replace('tab-', ''),
        start_page=start_page,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader,
        proxy_ip_port=proxy_ip_port,
        is_have_pages=(year not in no_pages_year),
        is_need_click_group_button=(year == 2018)
    )


def download_iclr_conditional_poster_papers(save_dir, year, base_url=None,
                              time_step_in_seconds=10, downloader='IDM',
                              start_page=1, proxy_ip_port=None):
    """
    Download iclr conditional poster papers for year 2025.
    :param save_dir: str, paper save path
    :param year: int, iclr year, current only support year >= 2018
    :param base_url: str, paper website url
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds.
    :param downloader: str, the downloader to download, could be 'IDM' or
        None, default to 'IDM'.
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Currently, this parameter is only used in year 2024.
        Default: 1.
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Default: None.
    :type proxy_ip_port: str | None
    :return:
    """
    group_id_dict = {
        2025: "tab-accept-conditional-poster"
    }
    if base_url is None:
        if year in group_id_dict:
            base_url = 'https://openreview.net/group?id=ICLR.cc/' \
                f'{year}/Conference#{group_id_dict[year]}'
        else:
            raise ValueError('the website url is not given for this year!')
    print(f'Downloading ICLR-{year} conditional poster papers...')
    group_id = group_id_dict[year].replace('tab-', '')
    download_iclr_papers_given_url_and_group_id(
        save_dir=save_dir,
        year=year,
        base_url=base_url,
        group_id=group_id,
        start_page=start_page,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader,
        proxy_ip_port=proxy_ip_port,
        is_have_pages=(year > 2021)
    )


def download_iclr_spotlight_papers(save_dir, year, base_url=None,
                                   time_step_in_seconds=10, downloader='IDM',
                                   start_page=1, proxy_ip_port=None):
    """
    Download iclr spotlight papers between year 2020 and 2022, 2024~2025.
    :param save_dir: str, paper save path
    :param year: int, iclr year, current only support year >= 2018
    :param base_url: str, paper website url
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds
    :param downloader: str, the downloader to download, could be 'IDM' or
        None, default to 'IDM'
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Currently, this parameter is only used in year 2024.
        Default: 1.
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Default: None.
    :return:
    """
    group_id_dict = {
        2025: "tab-accept-spotlight",
        2024: "tab-accept-spotlight",
        2022: "spotlight-submissions",
        2021: "spotlight-presentations",
        2020: "spotlight-presentations",
    }
    if base_url is None:
        if year in group_id_dict:
            base_url = 'https://openreview.net/group?id=ICLR.cc/' \
                f'{year}/Conference#{group_id_dict[year]}'
        else:
            raise ValueError('the website url is not given for this year!')
    print(f'Downloading ICLR-{year} spotlight papers...')
    no_pages_year = [2020, 2021]
    download_iclr_papers_given_url_and_group_id(
        save_dir=save_dir,
        year=year,
        base_url=base_url,
        group_id=group_id_dict[year].replace('tab-', ''),
        start_page=start_page,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader,
        proxy_ip_port=proxy_ip_port,
        is_have_pages=(year not in no_pages_year)
    )


def download_iclr_conditional_spotlight_papers(save_dir, year, base_url=None,
                              time_step_in_seconds=10, downloader='IDM',
                              start_page=1, proxy_ip_port=None):
    """
    Download iclr conditional spotlight papers for year 2025.
    :param save_dir: str, paper save path
    :param year: int, iclr year, current only support year >= 2018
    :param base_url: str, paper website url
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds.
    :param downloader: str, the downloader to download, could be 'IDM' or
        None, default to 'IDM'.
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Currently, this parameter is only used in year 2024.
        Default: 1.
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Default: None.
    :type proxy_ip_port: str | None
    :return:
    """
    group_id_dict = {
        2025: "tab-accept-conditional-spotlight"
    }
    no_pages_year = [2025]
    if base_url is None:
        if year in group_id_dict:
            base_url = 'https://openreview.net/group?id=ICLR.cc/' \
                f'{year}/Conference#{group_id_dict[year]}'
        else:
            raise ValueError('the website url is not given for this year!')
    print(f'Downloading ICLR-{year} conditional spotlight papers...')
    group_id = group_id_dict[year].replace('tab-', '')
    download_iclr_papers_given_url_and_group_id(
        save_dir=save_dir,
        year=year,
        base_url=base_url,
        group_id=group_id,
        start_page=start_page,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader,
        proxy_ip_port=proxy_ip_port,
        is_have_pages=(year not in no_pages_year)
    )


def download_iclr_top25_papers(save_dir, year, base_url=None, start_page=1,
                               time_step_in_seconds=10, downloader='IDM',
                               proxy_ip_port=None):
    """
    Download iclr notable-top-25% papers for year 2023.
    :param save_dir: str, paper save path
    :param year: int, iclr year
    :type year: int
    :param base_url: str, paper website url
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Default: 1
    :param time_step_in_seconds: int, the interval time between two downlaod
        request in seconds. Default: 10.
    :type time_step_in_seconds: int
    :param downloader: str, the downloader to download, could be 'IDM' or
        None. Default: 'IDM'.
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Default: None.
    :type proxy_ip_port: str | None
    :return:
    """
    if base_url is None:
        if year == 2023:
            base_url = "https://openreview.net/group?id=ICLR.cc/" \
                       "2023/Conference#notable-top-25-"
        else:
            raise ValueError('the website url is not given for this year!')
    print(f'Downloading ICLR-{year} top25 papers...')
    group_id = "notable-top-25-"
    download_iclr_papers_given_url_and_group_id(
        save_dir=save_dir,
        year=year,
        base_url=base_url,
        group_id=group_id,
        start_page=start_page,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader,
        proxy_ip_port=proxy_ip_port
    )


def download_iclr_paper(save_dir, year, base_url=None,
                        time_step_in_seconds=10, downloader='IDM',
                        start_page=1, proxy_ip_port=None):
    """
    Download iclr papers between year 2013 and 2024.
    :param save_dir: str, paper save path
    :param year: int, iclr year, current only support year >= 2018
    :param base_url: str, paper website url
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds.
    :param downloader: str, the downloader to download, could be 'IDM' or
        None, default to 'IDM'.
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Currently, this parameter is only used in year 2024.
        Default: 1.
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Default: None.
    :type proxy_ip_port: str | None
    :return:
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    year_no_group = [2014]
    year_no_group_iclrcc = [2015, 2016]
    year_oral_poster = [2013, 2017, 2018, 2019]
    year_oral_spotlight_poster = [2020, 2021, 2022, 2024, 2025]
    year_top5_top25_poster = [2023]
    year_oral_spotlight_poster_conditional = [2025]

    # no group, openreview website
    if year in year_no_group:
        if base_url is None:
            if year == 2014:
                base_url = 'https://openreview.net/group?id=ICLR.cc/2014/conference'
            else:
                raise ValueError('the website url is not given for this year!')
        print(f'Downloading ICLR-{year} oral papers...')
        group_id_dict = {
            2014: "submitted-papers"
        }
        group_id = group_id_dict[year]
        no_pages_year = [2014]
        return download_iclr_papers_given_url_and_group_id(
            save_dir=save_dir,
            year=year,
            base_url=base_url,
            group_id=group_id,
            start_page=start_page,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            proxy_ip_port=proxy_ip_port,
            is_have_pages=(year not in no_pages_year)
        )
    # no group, iclr.cc website
    if year in year_no_group_iclrcc:
        downloader = Downloader(downloader=downloader)
        paper_postfix = f'ICLR_{year}'
        if base_url is None:
            if year == 2016:
                base_url = 'https://iclr.cc/archive/www/doku.php%3Fid=iclr2016:main.html'
            elif year == 2015:
                base_url = 'https://iclr.cc/archive/www/doku.php%3Fid=iclr2015:main.html'
            elif year == 2014:
                base_url = 'https://iclr.cc/archive/2014/conference-proceedings/'
            else:
                raise ValueError('the website url is not given for this year!')
        os.makedirs(save_dir, exist_ok=True)
        if year == 2015:  # oral and poster seperated
            oral_save_path = os.path.join(save_dir, 'oral')
            poster_save_path = os.path.join(save_dir, 'poster')
            workshop_save_path = os.path.join(save_dir, 'ws')
            os.makedirs(oral_save_path, exist_ok=True)
            os.makedirs(poster_save_path, exist_ok=True)
            os.makedirs(workshop_save_path, exist_ok=True)
        dat_file_pathname = os.path.join(
            project_root_folder, 'urls', f'init_url_iclr_{year}.dat'
        )
        if os.path.exists(dat_file_pathname):
            with open(dat_file_pathname, 'rb') as f:
                content = pickle.load(f)
        else:
            headers = {
                'User-Agent':
                    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
                    'Gecko/20100101 Firefox/23.0'}
            req = urllib.request.Request(url=base_url, headers=headers)
            content = urllib.request.urlopen(req).read()
            with open(f'..\\urls\\init_url_iclr_{year}.dat', 'wb') as f:
                pickle.dump(content, f)
        error_log = []
        soup = BeautifulSoup(content, 'html.parser')
        print('open url successfully!')
        if year == 2016:
            papers = soup.find('h3',
                               {
                                   'id': 'accepted_papers_conference_track'}).findNext(
                'div').find_all('a')
            for paper in tqdm(papers):
                link = paper.get('href')
                if link.startswith('http://arxiv'):
                    title = slugify(paper.text)
                    pdf_name = f'{title}_{paper_postfix}.pdf'
                    try:
                        if not os.path.exists(
                                os.path.join(save_dir,
                                             title + f'_{paper_postfix}.pdf')):
                            pdf_link = get_pdf_link_from_arxiv(link)
                            print(f'downloading {title}')
                            downloader.download(
                                urls=pdf_link,
                                save_path=os.path.join(save_dir, pdf_name),
                                time_sleep_in_seconds=time_step_in_seconds
                            )
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append(
                            (title, link, 'paper download error', str(e)))
            # workshops
            papers = soup.find('h3',
                               {
                                   'id': 'workshop_track_posters_may_2nd'}).findNext(
                'div').find_all('a')
            for paper in tqdm(papers):
                link = paper.get('href')
                if link.startswith('http://beta.openreview'):
                    title = slugify(paper.text)
                    pdf_name = f'{title}_ICLR_WS_{year}.pdf'
                    try:
                        if not os.path.exists(
                                os.path.join(save_dir, 'ws', pdf_name)):
                            pdf_link = get_pdf_link_from_openreview(link)
                            print(f'downloading {title}')
                            downloader.download(
                                urls=pdf_link,
                                save_path=os.path.join(save_dir, 'ws',
                                                       pdf_name),
                                time_sleep_in_seconds=time_step_in_seconds
                            )
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append(
                            (title, link, 'paper download error', str(e)))
            papers = soup.find('h3',
                               {
                                   'id': 'workshop_track_posters_may_3rd'}).findNext(
                'div').find_all('a')
            for paper in tqdm(papers):
                link = paper.get('href')
                if link.startswith('http://beta.openreview'):
                    title = slugify(paper.text)
                    pdf_name = f'{title}_ICLR_WS_{year}.pdf'
                    try:
                        if not os.path.exists(
                                os.path.join(save_dir, 'ws', pdf_name)):
                            pdf_link = get_pdf_link_from_openreview(link)
                            print(f'downloading {title}')
                            downloader.download(
                                urls=pdf_link,
                                save_path=os.path.join(save_dir, 'ws',
                                                       pdf_name),
                                time_sleep_in_seconds=time_step_in_seconds
                            )
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append(
                            (title, link, 'paper download error', str(e)))
        elif year == 2015:
            # oral papers
            oral_papers = soup.find('h3', {
                'id': 'conference_oral_presentations'}).findNext(
                'div').find_all(
                'a')
            for paper in tqdm(oral_papers):
                link = paper.get('href')
                if link.startswith('http://arxiv'):
                    title = slugify(paper.text)
                    pdf_name = f'{title}_{paper_postfix}.pdf'
                    try:
                        if not os.path.exists(
                                os.path.join(oral_save_path,
                                             title + f'_{paper_postfix}.pdf')):
                            pdf_link = get_pdf_link_from_arxiv(link)
                            print(f'downloading {title}')
                            downloader.download(
                                urls=pdf_link,
                                save_path=os.path.join(oral_save_path,
                                                       pdf_name),
                                time_sleep_in_seconds=time_step_in_seconds
                            )
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append(
                            (title, link, 'paper download error', str(e)))

            # workshops papers
            workshop_papers = soup.find('h3', {
                'id': 'may_7_workshop_poster_session'}).findNext(
                'div').find_all(
                'a')
            workshop_papers.append(
                soup.find('h3',
                          {'id': 'may_8_workshop_poster_session'}).findNext(
                    'div').find_all('a'))
            for paper in tqdm(workshop_papers):
                link = paper.get('href')
                if link.startswith('http://arxiv'):
                    title = slugify(paper.text)
                    pdf_name = f'{title}_ICLR_WS_{year}.pdf'
                    try:
                        if not os.path.exists(
                                os.path.join(workshop_save_path,
                                             title + f'_{paper_postfix}.pdf')):
                            pdf_link = get_pdf_link_from_arxiv(link)
                            print(f'downloading {title}')
                            downloader.download(
                                urls=pdf_link,
                                save_path=os.path.join(workshop_save_path,
                                                       pdf_name),
                                time_sleep_in_seconds=time_step_in_seconds)
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append(
                            (title, link, 'paper download error', str(e)))
            # poster papers
            poster_papers = soup.find('h3', {
                'id': 'may_9_conference_poster_session'}).findNext(
                'div').find_all(
                'a')
            for paper in tqdm(poster_papers):
                link = paper.get('href')
                if link.startswith('http://arxiv'):
                    title = slugify(paper.text)
                    pdf_name = f'{title}_{paper_postfix}.pdf'
                    try:
                        if not os.path.exists(
                                os.path.join(poster_save_path,
                                             title + f'_{paper_postfix}.pdf')):
                            pdf_link = get_pdf_link_from_arxiv(link)
                            print(f'downloading {title}')
                            downloader.download(
                                urls=pdf_link,
                                save_path=os.path.join(poster_save_path,
                                                       pdf_name),
                                time_sleep_in_seconds=time_step_in_seconds)
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append(
                            (title, link, 'paper download error', str(e)))
        elif year == 2014:
            papers = soup.find('div',
                               {'id': 'sites-canvas-main-content'}).find_all(
                'a')
            for paper in tqdm(papers):
                link = paper.get('href')
                if link.startswith('http://arxiv'):
                    title = slugify(paper.text)
                    pdf_name = f'{title}_{paper_postfix}.pdf'
                    try:
                        if not os.path.exists(os.path.join(save_dir, pdf_name)):
                            pdf_link = get_pdf_link_from_arxiv(link)
                            print(f'downloading {title}')
                            downloader.download(
                                urls=pdf_link,
                                save_path=os.path.join(save_dir, pdf_name),
                                time_sleep_in_seconds=time_step_in_seconds)
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append(
                            (title, link, 'paper download error', str(e)))

            # workshops
            paper_postfix = f'ICLR_WS_{year}'
            base_url = 'https://sites.google.com/site/representationlearning2014/' \
                       'workshop-proceedings'
            headers = {
                'User-Agent':
                    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
                    'Gecko/20100101 Firefox/23.0'}
            req = urllib.request.Request(url=base_url, headers=headers)
            content = urllib.request.urlopen(req).read()
            soup = BeautifulSoup(content, 'html.parser')
            workshop_save_path = os.path.join(save_dir, 'WS')
            os.makedirs(workshop_save_path, exist_ok=True)
            papers = soup.find(
                'div', {'id': 'sites-canvas-main-content'}).find_all('a')
            for paper in tqdm(papers):
                link = paper.get('href')
                if link.startswith('http://arxiv'):
                    title = slugify(paper.text)
                    pdf_name = f'{title}_{paper_postfix}.pdf'
                    try:
                        if not os.path.exists(
                                os.path.join(workshop_save_path, pdf_name)):
                            pdf_link = get_pdf_link_from_arxiv(link)
                            print(f'downloading {title}')
                            downloader.download(
                                urls=pdf_link,
                                save_path=os.path.join(workshop_save_path,
                                                       pdf_name),
                                time_sleep_in_seconds=time_step_in_seconds)
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append(
                            (title, link, 'paper download error', str(e)))

        # write error log
        print('write error log')
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

    # oral openreview
    if year in (year_oral_poster + year_oral_spotlight_poster):
        save_dir_oral = os.path.join(save_dir, 'oral')
        download_iclr_oral_papers(
            save_dir_oral,
            year,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            start_page=start_page,
            proxy_ip_port=proxy_ip_port
        )
    
    # conditional oral openreview
    if year in (year_oral_spotlight_poster_conditional):
        save_dir_cond_oral = os.path.join(save_dir, 'conditional-oral')
        download_iclr_conditional_oral_papers(
            save_dir_cond_oral,
            year,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            start_page=start_page,
            proxy_ip_port=proxy_ip_port
        )

    # poster openreview
    if year in (year_oral_poster + year_oral_spotlight_poster +
                year_top5_top25_poster):
        save_dir_poster = os.path.join(save_dir, 'poster')
        download_iclr_poster_papers(
            save_dir_poster,
            year,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            start_page=start_page,
            proxy_ip_port=proxy_ip_port
        )
    
    # conditional poster openreview
    if year in (year_oral_spotlight_poster_conditional):
        save_dir_cond_poster = os.path.join(save_dir, 'conditional-poster')
        download_iclr_conditional_poster_papers(
            save_dir_cond_poster,
            year,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            start_page=start_page,
            proxy_ip_port=proxy_ip_port
        )

    # spotlight openreview
    if year in year_oral_spotlight_poster:
        save_dir_spotlight = os.path.join(save_dir, 'spotlight')
        download_iclr_spotlight_papers(
            save_dir_spotlight,
            year,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            start_page=start_page,
            proxy_ip_port=proxy_ip_port
        )

    # conditional spotlight openreview
    if year in (year_oral_spotlight_poster_conditional):
        save_dir_cond_spotlight = os.path.join(save_dir, 'conditional-spotlight')
        download_iclr_conditional_spotlight_papers(
            save_dir_cond_spotlight,
            year,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            start_page=start_page,
            proxy_ip_port=proxy_ip_port
        )

    # top5 openreview
    if year in year_top5_top25_poster:
        save_dir_top5 = os.path.join(save_dir, 'top5')
        download_iclr_top5_papers(
            save_dir_top5,
            year,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            start_page=start_page,
            proxy_ip_port=proxy_ip_port
        )

    # top25 openreview
    if year in year_top5_top25_poster:
        save_dir_top25 = os.path.join(save_dir, 'top25')
        download_iclr_top25_papers(
            save_dir_top25,
            year,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            start_page=start_page,
            proxy_ip_port=proxy_ip_port
        )


def get_pdf_link_from_openreview(abs_link):
    return abs_link.replace('beta.', '').replace('forum', 'pdf')


if __name__ == '__main__':
    year = 2025
    save_dir_iclr = rf'E:\ICLR_{year}'
    # save_dir_iclr_oral = os.path.join(save_dir_iclr, 'oral')
    # save_dir_iclr_top5 = os.path.join(save_dir_iclr, 'top5')
    # save_dir_iclr_spotlight = os.path.join(save_dir_iclr, 'spotlight')
    # save_dir_iclr_top25 = os.path.join(save_dir_iclr, 'top25')
    # save_dir_iclr_poster = os.path.join(save_dir_iclr, 'poster')
    proxy_ip_port = None
    # proxy_ip_port = "http://127.0.0.1:7890"
    # download_iclr_oral_papers(save_dir_iclr_oral, year,
    #                           time_step_in_seconds=5)
    # download_iclr_top5_papers(save_dir_iclr_top5, year, start_page=1,
    #                           time_step_in_seconds=5,
    #                           proxy_ip_port=proxy_ip_port)
    # download_iclr_top25_papers(save_dir_iclr_top25, year, start_page=1,
    #                           time_step_in_seconds=5,
    #                           proxy_ip_port=proxy_ip_port)
    # download_iclr_spotlight_papers(save_dir_iclr_spotlight, year,
    #                                time_step_in_seconds=5)
    # download_iclr_poster_papers(save_dir_iclr_poster, year, start_page=1,
    #                             time_step_in_seconds=5,
    #                           proxy_ip_port=proxy_ip_port)
    download_iclr_paper(save_dir_iclr, year, time_step_in_seconds=5,
                        proxy_ip_port=proxy_ip_port)
