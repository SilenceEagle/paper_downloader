"""paper_downloader_CORL.py"""
import os
import sys
root_folder = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
import lib.pmlr as pmlr


def download_paper(year, save_dir, is_download_supplement=False, time_step_in_seconds=5, downloader='IDM'):
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
    if year in CORL_year_dict.keys():
        volume = f'v{CORL_year_dict[year]}'
    else:
        raise ValueError('''the given year's url is unknown !''')
    postfix = f'CORL_{year}'

    pmlr.download_paper_given_volume(
        volume=volume,
        save_dir=save_dir,
        postfix=postfix,
        is_download_supplement=is_download_supplement,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader
    )


if __name__ == '__main__':
    for year in range(2023, 2024):
        download_paper(
            year,
            rf'E:\CORL\CORL_{year}',
            is_download_supplement=False,
            time_step_in_seconds=30,
            downloader='IDM'
            # downloader = None
        )
    pass
