"""paper_download_CVPR_IDM.py"""

import urllib
from urllib.request import urlopen
import time
from bs4 import BeautifulSoup
import pickle
from PyPDF3 import PdfFileMerger
import zipfile
import os
import shutil
from tqdm import tqdm
import subprocess
from slugify import slugify
import csv


def save_csv(year):
    """
    write CVPR conference papers' and supplemental material's urls in one csv file
    :param year: int
    :return: True
    """
    with open(f'CVPR_{year}.csv', 'w', newline='') as csvfile:
        fieldnames = ['title', 'main link', 'supplemental link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        init_url = f'http://openaccess.thecvf.com/CVPR{year}.py'
        if os.path.exists(f'init_url_CVPR_{year}.dat'):
            with open(f'init_url_CVPR_{year}.dat', 'rb') as f:
                content = pickle.load(f)
        else:
            # content = urlopen(init_url).read()
            content = open(f'..\\CVPR_{year}.html', 'rb').read()
            with open(f'init_url_CVPR_{year}.dat', 'wb') as f:
                pickle.dump(content, f)
        soup = BeautifulSoup(content, 'html5lib')
        paper_list_bar = tqdm(soup.find('div', {'id': 'content'}).find_all(['dd', 'dt']))
        paper_index = 0
        paper_dict = {'title': '',
                      'main link': '',
                      'supplemental link': ''}
        for paper in paper_list_bar:
            is_new_paper = False

            # get title
            try:
                if 'dt' == paper.name and 'ptitle' == paper.get('class')[0]:  # title:
                    title = slugify(paper.text.strip())
                    paper_dict['title'] = title
                    paper_index += 1
                    paper_list_bar.set_description_str(f'Downloading paper {paper_index}: {title}')
                elif 'dd' == paper.name:
                    all_as = paper.find_all('a')
                    for a in all_as:
                        if 'pdf' == slugify(a.text.strip()):
                            main_link = urllib.parse.urljoin(init_url, a.get('href'))
                            paper_dict['main link'] = main_link
                            is_new_paper = True
                        elif 'supp' == slugify(a.text.strip()):
                            supp_link = urllib.parse.urljoin(init_url, a.get('href'))
                            paper_dict['supplemental link'] = supp_link
                            break
            except:
                pass
            if is_new_paper:
                writer.writerow(paper_dict)
                paper_dict = {'title': '',
                              'main link': '',
                              'supplemental link': ''}
    return paper_index


def save_csv_workshops(year):
    """
    write CVPR workshops papers' and supplemental material's urls in one csv file
    :param year: int
    :return: True
    """
    with open(f'CVPR_WS_{year}.csv', 'w', newline='') as csvfile:
        fieldnames = ['group', 'title', 'main link', 'supplemental link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        init_url = f'http://openaccess.thecvf.com/CVPR{year}_workshops/menu'
        if os.path.exists(f'init_url_CVPR_WS_{year}.dat'):
            with open(f'init_url_CVPR_WS_{year}.dat', 'rb') as f:
                content = pickle.load(f)
        else:
            content = urlopen(init_url).read()
            # content = open(f'..\\CVPR_WS_{year}.html', 'rb').read()
            with open(f'init_url_CVPR_WS_{year}.dat', 'wb') as f:
                pickle.dump(content, f)
        soup = BeautifulSoup(content, 'html5lib')
        paper_group_list_bar = soup.find('div', {'id': 'content'}).find_all('dd')
        paper_index = 0
        paper_dict = {'group': '',
                      'title': '',
                      'main link': '',
                      'supplemental link': ''}
        for group in paper_group_list_bar:
            # get group name
            a = group.find('a')
            group_name = slugify(a.text)
            paper_dict['group'] = group_name
            print(f'GROUP: {group_name}')
            group_link = urllib.parse.urljoin(init_url, a.get('href'))
            group_content = urlopen(group_link).read()
            group_soup = BeautifulSoup(group_content, 'html5lib')
            paper_list_bar = tqdm(group_soup.find('div', {'id': 'content'}).find_all(['dd', 'dt']))
            for paper in paper_list_bar:
                is_new_paper = False

                # get title
                try:
                    if 'dt' == paper.name and 'ptitle' == paper.get('class')[0]:  # title:
                        title = slugify(paper.text.strip())
                        paper_dict['title'] = title
                        paper_index += 1
                        paper_list_bar.set_description_str(f'Downloading paper {paper_index}: {title}')
                    elif 'dd' == paper.name:
                        all_as = paper.find_all('a')
                        for a in all_as:
                            if 'pdf' == slugify(a.text.strip()):
                                main_link = urllib.parse.urljoin(group_link, a.get('href'))
                                paper_dict['main link'] = main_link
                                is_new_paper = True
                            elif 'supp' == slugify(a.text.strip()):
                                supp_link = urllib.parse.urljoin(init_url, a.get('href'))
                                paper_dict['supplemental link'] = supp_link
                                break
                except:
                    pass
                if is_new_paper:
                    writer.writerow(paper_dict)
                    paper_dict = {'group': group_name,
                                  'title': '',
                                  'main link': '',
                                  'supplemental link': ''}
    return paper_index


def download_from_csv(
        year, save_dir, is_download_supplement=True, time_step_in_seconds=5, total_paper_number=None,
        is_workshops=False):
    """
    download all CVPR paper and supplement files given year, restore in save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, CVPR year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental material
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :param total_paper_number: int, the total number of papers that is going to download
    :param is_workshops: bool, is to download workshops from csv file.
    :return: True
    """
    main_save_path = os.path.join(save_dir, 'main_paper')
    supplement_save_path = os.path.join(save_dir, 'supplement')
    os.makedirs(main_save_path, exist_ok=True)
    os.makedirs(supplement_save_path, exist_ok=True)
    # use IDM to download everything
    idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'''  # should replace by the local IDM path
    basic_command = [idm_path, '/d', 'xxxx', '/p', 'xxx', '/f', 'xxxx', '/n']

    error_log = []
    postfix = f'CVPR_{year}'
    if is_workshops:
        postfix = f'CVPR_WS_{year}'
    csv_file_name = f'CVPR_{year}.csv' if not is_workshops else f'CVPR_WS_{year}.csv'
    with open(csv_file_name, newline='') as csvfile:
        myreader = csv.DictReader(csvfile, delimiter=',')
        pbar = tqdm(myreader)
        i = 0
        for this_paper in pbar:
            i += 1
            # get title
            if is_workshops:
                group = slugify(this_paper['group'])
            title = slugify(this_paper['title'])
            if total_paper_number is not None:
                pbar.set_description(f'Downloading paper {i}/{total_paper_number}')

            else:
                pbar.set_description(f'Downloading paper {i}')

            this_paper_main_path = os.path.join(main_save_path, f'{title}_{postfix}.pdf')
            if is_workshops:
                this_paper_main_path = os.path.join(main_save_path, group, f'{title}_{postfix}.pdf')
            this_paper_supp_path_no_ext = os.path.join(supplement_save_path, f'{title}_{postfix}_supp.')
            if is_workshops:
                this_paper_supp_path_no_ext = os.path.join(supplement_save_path, group, f'{title}_{postfix}_supp.')
            if is_download_supplement:
                if '' != this_paper['supplemental link'] and os.path.exists(this_paper_main_path) and \
                        (os.path.exists(this_paper_supp_path_no_ext + 'zip') or os.path.exists(
                            this_paper_supp_path_no_ext + 'pdf')):
                    continue
                elif '' == this_paper['supplemental link'] and os.path.exists(this_paper_main_path):
                    continue
            else:
                if os.path.exists(this_paper_main_path):
                    continue
            if 'error' == this_paper['main link']:
                error_log.append((title, 'no MAIN link'))
            elif '' != this_paper['main link']:
                if is_workshops:
                    os.makedirs(os.path.join(main_save_path, group), exist_ok=True)
                    if is_download_supplement:
                        os.makedirs(os.path.join(supplement_save_path, group), exist_ok=True)
                try:
                    # download paper with IDM
                    if not os.path.exists(this_paper_main_path):
                        head, tail = os.path.split(this_paper_main_path)
                        basic_command[2] = this_paper['main link'].replace(' ', '%20')
                        basic_command[4] = head
                        basic_command[6] = tail
                        p = subprocess.Popen(' '.join(basic_command))
                        p.wait()
                        time.sleep(time_step_in_seconds)
                        # while True:
                        #     if os.path.exists(this_paper_main_path):
                        #         break
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
                                head, tail = os.path.split(this_paper_supp_path_no_ext)
                                basic_command[2] = this_paper['supplemental link']
                                basic_command[4] = head
                                basic_command[6] = tail + supp_type
                                p = subprocess.Popen(' '.join(basic_command))
                                p.wait()
                                time.sleep(time_step_in_seconds)
                            except Exception as e:
                                # error_flag = True
                                print('Error: ' + title + ' - ' + str(e))
                                error_log.append((title, this_paper['supplemental link'], 'supplement download error',
                                                  str(e)))

        # 2. write error log
        print('write error log')
        with open('download_err_log.txt', 'w') as f:
            for log in tqdm(error_log):
                for e in log:
                    if e is not None:
                        f.write(e)
                    else:
                        f.write('None')
                    f.write('\n')

                f.write('\n')


def merge_main_supplement(main_path, supplement_path, save_path, is_delete_ori_files=False):
    """
    merge the main paper and supplemental material into one single pdf file
    :param main_path: str, the main papers' path
    :param supplement_path: str, the supplemental material 's path
    :param save_path: str, merged pdf files's save path
    :param is_delete_ori_files: Bool, True for deleting the original main and supplemental material after merging
    """
    if not os.path.exists(main_path):
        raise ValueError(f'''can not open '{main_path}' !''')
    if not os.path.exists(supplement_path):
        raise ValueError(f'''can not open '{supplement_path}' !''')
    os.makedirs(save_path, exist_ok=True)
    error_log = []
    # make temp dir to unzip zip file
    temp_zip_dir = '.\\temp_zip'
    if not os.path.exists(temp_zip_dir):
        os.mkdir(temp_zip_dir)
    else:
        # remove all files
        for unzip_file in os.listdir(temp_zip_dir):
            if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                os.remove(os.path.join(temp_zip_dir, unzip_file))
            if os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
            else:
                print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
    paper_bar = tqdm(os.scandir(main_path))
    for paper in paper_bar:
        if paper.is_file():
            name, extension = os.path.splitext(paper.name)
            if '.pdf' == extension:
                paper_bar.set_description(f'''processing {name}''')
                if os.path.exists(os.path.join(save_path, paper.name)):
                    continue
                supp_pdf_path = None
                # error_floa = False
                if os.path.exists(os.path.join(supplement_path, f'{name}_supp.pdf')):
                    supp_pdf_path = os.path.join(supplement_path, f'{name}_supp.pdf')
                elif os.path.exists(os.path.join(supplement_path, f'{name}_supp.zip')):
                    try:
                        zip_ref = zipfile.ZipFile(os.path.join(supplement_path, f'{name}_supp.zip'), 'r')
                        zip_ref.extractall(temp_zip_dir)
                        zip_ref.close()
                    except Exception as e:
                        print('Error: ' + name + ' - ' + str(e))
                        error_log.append((paper.path, supp_pdf_path, str(e)))
                    try:
                        # find if there is a pdf file (by listing all files in the dir)
                        supp_pdf_list = [os.path.join(dp, f) for dp, dn, filenames in os.walk(temp_zip_dir) for f in filenames if f.endswith('pdf')]
                        # rename the first pdf file
                        if len(supp_pdf_list) >= 1:
                            # by default, we only deal with the first pdf
                            supp_pdf_path = os.path.join(supplement_path, name+'_supp.pdf')
                            if not os.path.exists(supp_pdf_path):
                                os.rename(supp_pdf_list[0], supp_pdf_path)
                        # empty the temp_folder (both the dirs and files)
                        for unzip_file in os.listdir(temp_zip_dir):
                            if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                                os.remove(os.path.join(temp_zip_dir, unzip_file))
                            elif os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                                shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
                            else:
                                print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
                    except Exception as e:
                        # error_floa = True
                        print('Error: ' + name + ' - ' + str(e))
                        error_log.append((paper.path, supp_pdf_path, str(e)))
                        # empty the temp_folder (both the dirs and files)
                        for unzip_file in os.listdir(temp_zip_dir):
                            if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                                os.remove(os.path.join(temp_zip_dir, unzip_file))
                            elif os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                                shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
                            else:
                                print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
                        continue
                if supp_pdf_path is not None:
                    try:
                        merger = PdfFileMerger()
                        f_handle1 = open(paper.path, 'rb')
                        merger.append(f_handle1)
                        f_handle2 = open(supp_pdf_path, 'rb')
                        merger.append(f_handle2)
                        with open(os.path.join(save_path, paper.name), 'wb') as fout:
                            merger.write(fout)
                            print('\tmerged!')
                        f_handle1.close()
                        f_handle2.close()
                        merger.close()
                        if is_delete_ori_files:
                            os.remove(paper.path)
                            if os.path.exists(os.path.join(supplement_path, f'{name}_supp.zip')):
                                os.remove(os.path.join(supplement_path, f'{name}_supp.zip'))
                            if os.path.exists(os.path.join(supplement_path, f'{name}_supp.pdf')):
                                os.remove(os.path.join(supplement_path, f'{name}_supp.pdf'))
                    except Exception as e:
                        print('Error: ' + name + ' - ' + str(e))
                        error_log.append((paper.path, supp_pdf_path, str(e)))
                        if os.path.exists(os.path.join(save_path, paper.name)):
                            os.remove(os.path.join(save_path, paper.name))

                else:
                    if is_delete_ori_files:
                        os.rename(paper.path, os.path.join(save_path, paper.name))
                    else:
                        shutil.copyfile(paper.path, os.path.join(save_path, paper.name))

    # 2. write error log
    print('write error log')
    with open('merge_err_log.txt', 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                if e is None:
                    f.write('None')
                else:
                    f.write(e)
                f.write('\n')

            f.write('\n')


def move_main_and_supplement_2_one_directory_WS(main_path, supplement_path):
    """
    merge the workshops main and supplemental material into main path
    :param main_path: str, the main papers' path
    :param supplement_path: str, the supplemental material 's path
    """
    if not os.path.exists(main_path):
        raise ValueError(f'''can not open '{main_path}' !''')
    if not os.path.exists(supplement_path):
        raise ValueError(f'''can not open '{supplement_path}' !''')
    error_log = []
    # make temp dir to unzip zip file
    temp_zip_dir = '.\\temp_zip'
    if not os.path.exists(temp_zip_dir):
        os.mkdir(temp_zip_dir)
    else:
        # remove all files
        for unzip_file in os.listdir(temp_zip_dir):
            if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                os.remove(os.path.join(temp_zip_dir, unzip_file))
            if os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
            else:
                print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
    for group in os.scandir(main_path):
        if group.is_dir():
            paper_bar = tqdm(os.scandir(group.path))
            for paper in paper_bar:
                if paper.is_file():
                    name, extension = os.path.splitext(paper.name)
                    if '.pdf' == extension:
                        paper_bar.set_description(f'''processing {name}''')
                        supp_pdf_path = None
                        # error_floa = False
                        if os.path.exists(os.path.join(supplement_path, group.name, f'{name}_supp.pdf')):
                            supp_pdf_path = os.path.join(supplement_path, group.name,  f'{name}_supp.pdf')
                            shutil.move(supp_pdf_path, os.path.join(main_path, group.name,  f'{name}_supp.pdf'))
                        elif os.path.exists(os.path.join(supplement_path, group.name, f'{name}_supp.zip')):
                            try:
                                zip_ref = zipfile.ZipFile(
                                    os.path.join(supplement_path, group.name, f'{name}_supp.zip'), 'r')
                                zip_ref.extractall(temp_zip_dir)
                                zip_ref.close()
                            except Exception as e:
                                print('Error: ' + name + ' - ' + str(e))
                                error_log.append((paper.path, supp_pdf_path, str(e)))
                            try:
                                # find if there is a pdf file (by listing all files in the dir)
                                supp_pdf_list = [os.path.join(dp, f) for dp, dn, filenames in os.walk(temp_zip_dir)
                                                 for f in filenames if f.endswith('pdf')]
                                # rename the first pdf file
                                if len(supp_pdf_list) >= 1:
                                    # by default, we only deal with the first pdf
                                    supp_pdf_path = os.path.join(main_path, group.name, name+'_supp.pdf')
                                    if not os.path.exists(supp_pdf_path):
                                        os.rename(supp_pdf_list[0], supp_pdf_path)
                                # empty the temp_folder (both the dirs and files)
                                for unzip_file in os.listdir(temp_zip_dir):
                                    if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                                        os.remove(os.path.join(temp_zip_dir, unzip_file))
                                    elif os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                                        shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
                                    else:
                                        print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
                            except Exception as e:
                                print('Error: ' + name + ' - ' + str(e))
                                error_log.append((paper.path, supp_pdf_path, str(e)))

    # 2. write error log
    print('write error log')
    with open('merge_err_log.txt', 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                if e is None:
                    f.write('None')
                else:
                    f.write(e)
                f.write('\n')

            f.write('\n')


if __name__ == '__main__':
    pass
