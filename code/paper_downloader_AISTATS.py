"""paper_downloader_AISTATS.py"""
import os
import sys
root_folder = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
import lib.pmlr as pmlr
from lib.supplement_porcess import merge_main_supplement, move_main_and_supplement_2_one_directory, \
    move_main_and_supplement_2_one_directory_with_group
from lib.openreview import download_papers_given_url_and_group_id


def download_paper(
        year, save_dir, is_download_supplement=True, time_step_in_seconds=5, 
        source='pmlr', downloader='IDM'):
    """
    download all AISTATS paper and supplement files given year, restore in
    save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, AISTATS year, such as 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental
        material
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds
    :param source: str, the source of the papers, could be 'pmlr' or
        'openreview', default to 'pmlr'
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder', default to 'IDM'
    :return: True
    """
    assert source in ['pmlr', 'openreview'], \
        f'only support source pmlr or openreview, but get {source}'
    # pmlr
    AISTATS_year_dict = {
        2025: 258,
        2024: 238,
        2023: 206,
        2022: 151,
        2021: 130,
        2020: 108,
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
        1995: 0,
        1997: 1,
        1999: 2,
        2001: 3,
        2003: 4,
        2005: 5

    }
    # openreview
    year_poster = [2026]
    year_oral = [2026]
    year_spotlight = [2026]

    if source == 'pmlr':
        if year in AISTATS_year_dict.keys():
            volume = f'v{AISTATS_year_dict[year]}'
        elif year in AISTATS_year_dict_R.keys():
            volume = f'r{AISTATS_year_dict_R[year]}'
        else:
            raise ValueError('''the given year's url is unknown (PMLR)!''')
        postfix = f'AISTATS_{year}'

        pmlr.download_paper_given_volume(
            volume=volume,
            save_dir=save_dir,
            postfix=postfix,
            is_download_supplement=is_download_supplement,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader
        )
    else: # source == 'openreview'
        if year in year_oral:  # oral
            download_aistats_oral_papers(
                save_dir=save_dir,
                year=year,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader
            )
        if year in year_spotlight:  # spotlight
            download_aistats_spotlight_papers(
                save_dir=save_dir,
                year=year,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader
            )
        if year in year_poster:  # poster
            download_aistats_poster_papers(
                save_dir=save_dir,
                year=year,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader
            )


def download_aistats_poster_papers(save_dir, year, base_url=None, start_page=1,
                                time_step_in_seconds=10, downloader='IDM',
                                proxy_ip_port=None):
    """
    Download aistats poster papers from year 2026 from openreview.
    :param save_dir: str, paper save path
    :param year: int, aistats year, current only support year
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
        2026: "tab-accept-poster",
    }
    if base_url is None:
        if year in group_id_dict:
            base_url = 'https://openreview.net/group?id=aistats.org/AISTATS/' \
                f'{year}/Conference#{group_id_dict[year]}'
        else:
            raise ValueError('the website url is not given for this year!')
    print(f'Downloading AISTATS-{year} poster papers...')
    no_pages_year = []
    save_dir = os.path.join(save_dir, 'poster') 
    download_papers_given_url_and_group_id(
        save_dir=save_dir,
        year=year,
        base_url=base_url,
        group_id=group_id_dict[year].replace('tab-', ''),
        conference='AISTATS',
        start_page=start_page,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader,
        proxy_ip_port=proxy_ip_port,
        is_have_pages=(year not in no_pages_year),
        is_need_click_group_button=(year == 2018)
    )


def download_aistats_oral_papers(save_dir, year, base_url=None, start_page=1,
                                time_step_in_seconds=10, downloader='IDM',
                                proxy_ip_port=None):
    """
    Download aistats oral papers from year 2026 from openreview.
    :param save_dir: str, paper save path
    :param year: int, aistats year, current only support year
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
        2026: "tab-accept-oral",
    }
    if base_url is None:
        if year in group_id_dict:
            base_url = 'https://openreview.net/group?id=aistats.org/AISTATS/' \
                f'{year}/Conference#{group_id_dict[year]}'
        else:
            raise ValueError('the website url is not given for this year!')
    print(f'Downloading AISTATS-{year} oral papers...')
    no_pages_year = [2026]
    save_dir = os.path.join(save_dir, 'oral') 
    download_papers_given_url_and_group_id(
        save_dir=save_dir,
        year=year,
        base_url=base_url,
        group_id=group_id_dict[year].replace('tab-', ''),
        conference='AISTATS',
        start_page=start_page,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader,
        proxy_ip_port=proxy_ip_port,
        is_have_pages=(year not in no_pages_year),
        is_need_click_group_button=(year == 2018)
    )


def download_aistats_spotlight_papers(save_dir, year, base_url=None, start_page=1,
                                time_step_in_seconds=10, downloader='IDM',
                                proxy_ip_port=None):
    """
    Download aistats spotlight papers from year 2026 from openreview.
    :param save_dir: str, paper save path
    :param year: int, aistats year, current only support year
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
        2026: "tab-accept-spotlight",
    }
    if base_url is None:
        if year in group_id_dict:
            base_url = 'https://openreview.net/group?id=aistats.org/AISTATS/' \
                f'{year}/Conference#{group_id_dict[year]}'
        else:
            raise ValueError('the website url is not given for this year!')
    print(f'Downloading AISTATS-{year} spotlight papers...')
    no_pages_year = []
    save_dir = os.path.join(save_dir, 'spotlight') 
    download_papers_given_url_and_group_id(
        save_dir=save_dir,
        year=year,
        base_url=base_url,
        group_id=group_id_dict[year].replace('tab-', ''),
        conference='AISTATS',
        start_page=start_page,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader,
        proxy_ip_port=proxy_ip_port,
        is_have_pages=(year not in no_pages_year),
        is_need_click_group_button=(year == 2018)
    )



if __name__ == '__main__':
    year = 2026
    download_paper(
        year,
        rf'D:\AISTATS_{year}',
        is_download_supplement=True,
        time_step_in_seconds=25,
        downloader='IDM',
        source='openreview'
    )
    # move_main_and_supplement_2_one_directory(
    #     main_path=rf'D:\AISTATS_{year}\main_paper',
    #     supplement_path=rf'D:\AISTATS_{year}\supplement',
    #     supp_pdf_save_path=rf'D:\AISTATS_{year}\supplement_pdf'
    # )
    pass
