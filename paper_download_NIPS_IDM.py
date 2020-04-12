"""paper_download_NIPS_IDM.py"""

from urllib.request import urlopen
import time
from bs4 import BeautifulSoup
import pickle
# from PyPDF2 import PdfFileMerger
from PyPDF3 import PdfFileMerger
import zipfile
import os
import shutil
from tqdm import tqdm
import subprocess
from slugify import slugify
import csv


def download_paper_and_sup_IDM(year, save_dir, is_download_supplement=True):
    """
    download all NIPS paper and supplement files given year, restore in save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, NIPS year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental material
    :return: True
    """
    init_url = f'http://papers.nips.cc/book/advances-in-neural-information-processing-systems-{year-1987}-{year}'
    main_save_path = os.path.join(save_dir, 'main_paper')
    supplement_save_path = os.path.join(save_dir, 'supplement')
    os.makedirs(main_save_path, exist_ok=True)
    os.makedirs(supplement_save_path, exist_ok=True)
    # use IDM to download everything
    idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'''  # should replace by the local IDM path
    basic_command = [idm_path, '/d', 'xxxx', '/p', os.getcwd(), '/f', 'xxxx', '/n']
    # create current dict
    title_list = []
    # paper_dict = dict()

    paper_website = 'http://papers.nips.cc'
    postfix = f'NIPS_{year}'
    if os.path.exists(f'init_url_nips_{year}.dat'):
        with open(f'init_url_nips_{year}.dat', 'rb') as f:
            content = pickle.load(f)
    else:
        content = urlopen(init_url).read()
        with open(f'init_url_nips_{year}.dat', 'wb') as f:
            pickle.dump(content, f)
    soup = BeautifulSoup(content, 'html.parser')
    temp_soup = soup.find_all('ul')[1]  # after the book section
    paper_list = temp_soup.find_all('li')
    error_log = []
    # num_download = 5 # number of papers to download
    num_download = len(paper_list)
    for paper in tqdm(zip(paper_list, range(num_download))):
        # get title
        print('\n')
        this_paper = paper[0]
        title = slugify(this_paper.a.text)
        try:
            print('Downloading paper {}/{}: {}'.format(paper[1]+1, num_download, title))
        except:
            print(title.encode('utf8'))
        title_list.append(title)

        # try:
        #     asc_title = title.encode('utf-8').decode('ascii')
        # except:
        #     print('has non english characters, canceled!')
        #     continue

        this_paper_main_path = os.path.join(main_save_path, f'{title}_{postfix}.pdf')
        this_paper_supp_path_no_ext = os.path.join(supplement_save_path, f'{title}_{postfix}_supp.')
        if is_download_supplement:
            if os.path.exists(this_paper_main_path) and \
                (os.path.exists(this_paper_supp_path_no_ext+'zip') or os.path.exists(this_paper_supp_path_no_ext+'pdf')):
                continue
        else:
            if os.path.exists(this_paper_main_path):
                continue

        # get abstract page url
        url2 = this_paper.a.get('href')

        # try 1 time
        # error_flag = False
        timeout_seconds = 50
        for d_iter in range(1):
            try:
                abs_content = urlopen(paper_website + url2, timeout=timeout_seconds).read()
                soup_temp = BeautifulSoup(abs_content, 'html.parser')
                # abstract = soup_temp.find('p', {'class': 'abstract'}).text.strip()
                # paper_dict[title] = abstract
                all_a = soup_temp.findAll('a')
                paper_link = None
                supp_link = None
                for a in all_a[4:9]:
                    if '[PDF]' == a.text:
                        paper_link = a.get('href')
                    elif '[Supplemental]' == a.text:
                        supp_link = a.get('href')
                        supp_type = supp_link.split('.')[-1]
                        break
                # paper_link = soup_temp.findAll('a')[4].get('href')
                # supp_link = soup_temp.findAll('a')[6].get('href')
                # supp_type = supp_link.split('.')[-1]
            except Exception as e:
                error_flag = True
                print('Error: ' + title + ' - ' + str(e))
                error_log.append((title, paper_website + url2, 'main paper url error',str(e)))
                continue
            try:
                # download paper with IDM
                if not os.path.exists(this_paper_main_path):
                    basic_command[2] = paper_website + paper_link
                    basic_command[6] = this_paper_main_path
                    p = subprocess.Popen(' '.join(basic_command))
                    p.wait()
                    time.sleep(3)
                    # while True:
                    #     if os.path.exists(this_paper_main_path):
                    #         break
            except Exception as e:
                # error_flag = True
                print('Error: ' + title + ' - ' + str(e))
                error_log.append((title, paper_website + url2, 'main paper download error', str(e)))
            # download supp
            if is_download_supplement:
                # check whether the supp can be downloaded
                if not (os.path.exists(this_paper_supp_path_no_ext + 'zip') or
                        os.path.exists(this_paper_supp_path_no_ext + 'pdf')):
                    # try:
                    #     req = urlopen(paper_website + supp_link, None, timeout_seconds)  # 5 seconds timeout
                    #     no_supp = False
                    # except Exception as e:
                    #     try:
                    #         no_supp = e.code == 404
                    #     except:
                    #         # error_flag = True
                    #         print('Error: ' + title + ' - ' + str(e))
                    #         error_log.append((title, paper_website + supp_link, 'supplement url error', str(e)))
                    #         continue
                    try:
                        # if not no_supp:
                        if supp_link is not None:
                            basic_command[2] = paper_website + supp_link
                            basic_command[6] = this_paper_supp_path_no_ext + supp_type
                            p = subprocess.Popen(' '.join(basic_command))
                            p.wait()
                            time.sleep(3)
                            # while True:
                            #     if os.path.exists(this_paper_supp_path_no_ext + supp_type):
                            #         break
                    except Exception as e:
                        # error_flag = True
                        print('Error: ' + title + ' - ' + str(e))
                        error_log.append((title, paper_website + supp_link, 'supplement download error', str(e)))

        # if error_flag:
        #     # paper_dict[title] = '\n'
        #     error_log.append((title, paper_website + url2))

    # store the results
    # 1. store in the pickle file
    # with open(f'{postfix}_pre.dat', 'wb') as f:
    #     pickle.dump(paper_dict, f)

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
                error_floa = False
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
                        error_floa = True
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
                if supp_pdf_path is not None and not error_floa:
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


def save_csv(year):
    """
    write nips papers' and supplemental material's urls in one csv file
    :param year: int
    :return: True
    """
    with open(f'NIPS_{year}.csv', 'w', newline='') as csvfile:
        fieldnames = ['title', 'main link', 'supplemental link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        init_url = f'http://papers.nips.cc/book/advances-in-neural-information-processing-systems-{year - 1987}-{year}'
        paper_website = 'http://papers.nips.cc'
        if os.path.exists(f'init_url_nips_{year}.dat'):
            with open(f'init_url_nips_{year}.dat', 'rb') as f:
                content = pickle.load(f)
        else:
            content = urlopen(init_url).read()
            with open(f'init_url_nips_{year}.dat', 'wb') as f:
                pickle.dump(content, f)
        soup = BeautifulSoup(content, 'html.parser')
        temp_soup = soup.find_all('ul')[1]  # after the book section
        paper_list = temp_soup.find_all('li')
        # num_download = 5 # number of papers to download
        num_download = len(paper_list)
        for paper in tqdm(zip(paper_list, range(num_download))):
            paper_dict = {'title': '',
                          'main link': '',
                          'supplemental link': ''}
            # get title
            print('\n')
            this_paper = paper[0]
            title = slugify(this_paper.a.text)
            paper_dict['title'] = title
            print('Downloading paper {}/{}: {}'.format(paper[1] + 1, num_download, title))

            # get abstract page url
            url2 = this_paper.a.get('href')
            try:
                abs_content = urlopen(paper_website + url2, timeout=50).read()
                soup_temp = BeautifulSoup(abs_content, 'html.parser')
                # abstract = soup_temp.find('p', {'class': 'abstract'}).text.strip()
                # paper_dict[title] = abstract
                all_a = soup_temp.findAll('a')
                for a in all_a[4:9]:
                    if '[PDF]' == a.text:
                        paper_dict['main link'] = paper_website + a.get('href')
                    elif '[Supplemental]' == a.text:
                        paper_dict['supplemental link'] = paper_website + a.get('href')
                        break
            except Exception as e:
                print('Error: ' + title + ' - ' + str(e))
                if paper_dict['main link'] == '':
                    paper_dict['main link'] = 'error'
                if paper_dict['supplemental link'] == '':
                    paper_dict['supplemental link'] = 'error'
            writer.writerow(paper_dict)
            time.sleep(2)


def download_from_csv(year, save_dir, is_download_supplement=True):
    """
    download all NIPS paper and supplement files given year, restore in save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, NIPS year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental material
    :return: True
    """
    main_save_path = os.path.join(save_dir, 'main_paper')
    supplement_save_path = os.path.join(save_dir, 'supplement')
    os.makedirs(main_save_path, exist_ok=True)
    os.makedirs(supplement_save_path, exist_ok=True)
    # use IDM to download everything
    idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'''  # should replace by the local IDM path
    basic_command = [idm_path, '/d', 'xxxx', '/p', os.getcwd(), '/f', 'xxxx', '/n']

    error_log = []
    paper_website = 'http://papers.nips.cc'
    postfix = f'NIPS_{year}'
    with open(f'NIPS_{year}.csv', newline='') as csvfile:
        myreader = csv.DictReader(csvfile, delimiter=',')
        pbar = tqdm(myreader)
        i = 0
        for this_paper in pbar:
            i += 1
            # get title
            print('\n')
            title = slugify(this_paper['title'])
            # print('Downloading paper {}: {}'.format(i, title))
            pbar.set_description(f'Downloading paper {i}')

            this_paper_main_path = os.path.join(main_save_path, f'{title}_{postfix}.pdf')
            this_paper_supp_path_no_ext = os.path.join(supplement_save_path, f'{title}_{postfix}_supp.')
            if is_download_supplement:
                if os.path.exists(this_paper_main_path) and \
                        (os.path.exists(this_paper_supp_path_no_ext + 'zip') or os.path.exists(
                            this_paper_supp_path_no_ext + 'pdf')):
                    continue
            else:
                if os.path.exists(this_paper_main_path):
                    continue
            if 'error' == this_paper['main link']:
                error_log.append((title, 'no MAIN link'))
            elif '' != this_paper['main link']:
                try:
                    # download paper with IDM
                    if not os.path.exists(this_paper_main_path):
                        basic_command[2] = this_paper['main link']
                        basic_command[6] = this_paper_main_path
                        p = subprocess.Popen(' '.join(basic_command))
                        p.wait()
                        time.sleep(5)
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
                                basic_command[2] = this_paper['supplemental link']
                                basic_command[6] = this_paper_supp_path_no_ext + supp_type
                                p = subprocess.Popen(' '.join(basic_command))
                                p.wait()
                                time.sleep(5)
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


if __name__ == '__main__':
    # year = 2011
    # download_paper_and_sup_IDM(year, f'..\\NIPS_{year}', is_download_supplement=True)
    # merge_main_supplement(main_path=f'..\\NIPS_{year}\main_paper',
    #                       supplement_path=f'..\\NIPS_{year}\supplement',
    #                       save_path=f'..\\NIPS_{year}',
    #                       is_delete_ori_files=True)
    # download_from_csv(year, f'..\\NIPS_{year}', is_download_supplement=True)
    for year in range(2010, 1987, -1):
        print(year)
        save_csv(year)
    pass
