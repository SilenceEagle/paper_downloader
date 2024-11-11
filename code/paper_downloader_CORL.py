"""paper_downloader_CORL.py"""
import os
import sys
root_folder = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
import lib.pmlr as pmlr
import lib.openreview as openreview


def download_paper(year, save_dir, is_download_supplement=False, 
                   time_step_in_seconds=5, downloader='IDM',
                   source=None, proxy_ip_port=None):
    """
    download all CORL paper and supplement files given year, restore in
    save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, CORL year, such as 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental
        material
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder', default to 'IDM'
    :param source: str, download source, support "pmlr" and "openreview". 
        Defaults to None, means first try to download from pmlr. If failed, 
        then try to download from openreview.
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890".  Only useful for webdriver and request
        downloader (downloader=None). Default: None.
    :type proxy_ip_port: str | None
    :return: True
    """
    CORL_year_dict = {
        2023: 229,
        2022: 205,
        2021: 164,
        2020: 155,
        2019: 100,
        2018: 87,
        2017: 78
    }
    postfix = f'CORL_{year}'

    if source != 'openreview':
        if year in CORL_year_dict.keys():  # download from pmlr
            volume = f'v{CORL_year_dict[year]}'
            pmlr.download_paper_given_volume(
                volume=volume,
                save_dir=save_dir,
                postfix=postfix,
                is_download_supplement=is_download_supplement,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader
            )
            return True
        elif source == 'pmlr':
            raise ValueError(f'Not found CoRL {year} in pmlr!')
        
    # try to download from openreview
    base_url = f'https://openreview.net/group?id=robot-learning.org/'\
               f'CoRL/{year}/Conference'
    group_id_dict = {
        2023: ['accept--oral-', 'accept--poster-'],
        2024: ['accept']
    }
    for gid in group_id_dict[year]:
        openreview.download_papers_given_url_and_group_id(
            save_dir=save_dir,
            year=year,
            base_url=f'{base_url}#{gid}',
            group_id=gid,
            conference='CORL',
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            proxy_ip_port=proxy_ip_port
        )
    return True 


if __name__ == '__main__':
    for year in range(2024, 2025):
        download_paper(
            year,
            rf'E:\CORL\CORL_{year}',
            is_download_supplement=False,
            time_step_in_seconds=30,
            downloader='IDM'
            # downloader = None
        )
    pass
