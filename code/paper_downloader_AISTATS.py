"""paper_downloader_AISTATS.py"""
import os
import sys
root_folder = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
import lib.pmlr as pmlr
from lib.supplement_porcess import merge_main_supplement, move_main_and_supplement_2_one_directory, \
    move_main_and_supplement_2_one_directory_with_group


def download_paper(year, save_dir, is_download_supplement=True, time_step_in_seconds=5, downloader='IDM'):
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
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder', default to 'IDM'
    :return: True
    """
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
    if year in AISTATS_year_dict.keys():
        volume = f'v{AISTATS_year_dict[year]}'
    elif year in AISTATS_year_dict_R.keys():
        volume = f'r{AISTATS_year_dict_R[year]}'
    else:
        raise ValueError('''the given year's url is unknown !''')
    postfix = f'AISTATS_{year}'

    pmlr.download_paper_given_volume(
        volume=volume,
        save_dir=save_dir,
        postfix=postfix,
        is_download_supplement=is_download_supplement,
        time_step_in_seconds=time_step_in_seconds,
        downloader=downloader
    )


if __name__ == '__main__':
    year = 2025
    download_paper(
        year,
        rf'D:\AISTATS_{year}',
        is_download_supplement=True,
        time_step_in_seconds=25,
        downloader='IDM'
    )
    # move_main_and_supplement_2_one_directory(
    #     main_path=rf'D:\AISTATS_{year}\main_paper',
    #     supplement_path=rf'D:\AISTATS_{year}\supplement',
    #     supp_pdf_save_path=rf'D:\AISTATS_{year}\supplement_pdf'
    # )
    pass
