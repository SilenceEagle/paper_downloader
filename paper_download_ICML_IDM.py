"""paper_download_ICML_IDM.py"""

import urllib
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


def download_paper_and_sup_IDM(year, save_dir, is_download_supplement=True, time_step_in_seconds=5):
    """
    download all ICML paper and supplement files given year, restore in save_dir/main_paper and save_dir/supplement
    respectively
    :param year: int, ICML year, such 2019
    :param save_dir: str, paper and supplement material's save path
    :param is_download_supplement: bool, True for downloading supplemental material
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :return: True
    """
    icml_year_dict = {2019: 97,
                      2018: 80,
                      2017: 70,
                      2016: 48,
                      2015: 37,
                      2014: 32,
                      2013: 28
                      }
    if year >= 2013 and year <= 2019:
        init_url = f'http://proceedings.mlr.press/v{icml_year_dict[year]}/'
    elif year == 2012:
        init_url = 'https://icml.cc/2012/papers.1.html'
    elif year == 2011:
        init_url = 'http://www.icml-2011.org/papers.php'
    elif 2009 == year:
        init_url = 'https://icml.cc/Conferences/2009/abstracts.html'
    elif 2008 == year:
        init_url = 'http://www.machinelearning.org/archive/icml2008/abstracts.shtml'
    elif 2007 == year:
        init_url = 'https://icml.cc/Conferences/2007/paperlist.html'
    elif year in [2006, 2004, 2005]:
        init_url = f'https://icml.cc/Conferences/{year}/proceedings.html'
    elif 2003 == year:
        init_url = 'https://aaai.org/Library/ICML/icml03contents.php'
    else:
        raise ValueError('''the given year's url is unknown !''')
    # init_url = f'http://papers.nips.cc/book/advances-in-neural-information-processing-systems-{year-1987}-{year}'

    # use IDM to download everything
    idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'''  # should replace by the local IDM path
    basic_command = [idm_path, '/d', 'xxxx', '/p', os.getcwd(), '/f', 'xxxx', '/n']  # silent /n
    # create current dict
    title_list = []
    # paper_dict = dict()

    postfix = f'ICML_{year}'
    if os.path.exists(f'init_url_icml_{year}.dat'):
        with open(f'init_url_icml_{year}.dat', 'rb') as f:
            content = pickle.load(f)
    else:
        # content = urlopen(init_url).read()
        content = open(f'..\\ICML_{year}.html', 'rb').read()
        with open(f'init_url_icml_{year}.dat', 'wb') as f:
            pickle.dump(content, f)
    # soup = BeautifulSoup(content, 'html.parser')
    soup = BeautifulSoup(content, 'html5lib')
    # soup = BeautifulSoup(open(r'..\ICML_2011.html', 'rb'), 'html.parser')
    error_log = []
    if year >= 2013:
        main_save_path = os.path.join(save_dir, 'main_paper')
        supplement_save_path = os.path.join(save_dir, 'supplement')
        os.makedirs(main_save_path, exist_ok=True)
        os.makedirs(supplement_save_path, exist_ok=True)
        paper_list = soup.find_all('div', {'class': 'paper'})
        # num_download = 5 # number of papers to download
        num_download = len(paper_list)
        for paper in tqdm(zip(paper_list, range(num_download))):
            # get title
            print('\n')
            this_paper = paper[0]
            title = slugify(this_paper.find_all('p', {'class': 'title'})[0].text)
            try:
                print('Downloading paper {}/{}: {}'.format(paper[1]+1, num_download, title))
            except:
                print(title.encode('utf8'))
            title_list.append(title)

            this_paper_main_path = os.path.join(main_save_path, f'{title}_{postfix}.pdf'.replace(' ', '_'))
            this_paper_supp_path = os.path.join(supplement_save_path, f'{title}_{postfix}_supp.pdf')
            this_paper_supp_path_no_ext = os.path.join(supplement_save_path, f'{title}_{postfix}_supp.')
            if is_download_supplement:
                if os.path.exists(this_paper_main_path) and os.path.exists(this_paper_supp_path):
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
                elif 'Supplementary PDF' == link.text or 'Supplementary Material' == link.text or \
                        'supplementary' == link.text:
                    supp_link = link.get('href')
                    if supp_link[-3:] != 'pdf':
                        this_paper_supp_path = this_paper_supp_path_no_ext + supp_link[-3:]


            # try 1 time
            # error_flag = False
            for d_iter in range(1):
                try:
                    # download paper with IDM
                    if not os.path.exists(this_paper_main_path) and main_link is not None:
                        basic_command[2] = main_link
                        basic_command[6] = this_paper_main_path
                        p = subprocess.Popen(' '.join(basic_command))
                        p.wait()
                        time.sleep(time_step_in_seconds)
                        # while True:
                        #     if os.path.exists(this_paper_main_path):
                        #         break
                except Exception as e:
                    # error_flag = True
                    print('Error: ' + title + ' - ' + str(e))
                    error_log.append((title, main_link, 'main paper download error', str(e)))
                # download supp
                if is_download_supplement:
                    # check whether the supp can be downloaded
                    if not os.path.exists(this_paper_supp_path) and supp_link is not None:
                        try:
                            basic_command[2] = supp_link
                            basic_command[6] = this_paper_supp_path
                            p = subprocess.Popen(' '.join(basic_command))
                            p.wait()
                            time.sleep(time_step_in_seconds)
                            # while True:
                            #     if os.path.exists(this_paper_supp_path_no_ext + supp_type):
                            #         break
                        except Exception as e:
                            # error_flag = True
                            print('Error: ' + title + ' - ' + str(e))
                            error_log.append((title, supp_link, 'supplement download error', str(e)))
    elif 2012 == year: # 2012
        base_url = f'https://icml.cc/{year}/'
        paper_list_bar = tqdm(soup.find_all('div', {'class': 'paper'}))
        paper_index = 0
        for paper in paper_list_bar:
            paper_index += 1
            title = ''
            title = slugify(paper.find('h2').text)
            link = None
            for a in paper.find_all('a'):
                if 'ICML version (pdf)' == a.text:
                    link = base_url + a.get('href')
                    break
            if link is not None:
                this_paper_main_path = os.path.join(save_dir, f'{title}_{postfix}.pdf'.replace(' ', '_'))
                paper_list_bar.set_description(f'find paper {paper_index}:{title}')
                if not os.path.exists(this_paper_main_path) :
                    paper_list_bar.set_description(f'downloading paper {paper_index}:{title}')
                    basic_command[2] = link
                    basic_command[6] = this_paper_main_path
                    p = subprocess.Popen(' '.join(basic_command))
                    p.wait()
                    time.sleep(time_step_in_seconds)
            else:
                error_log.append((title, 'no main link error'))
    elif 2011 == year:
        base_url = f'http://www.icml-{year}.org/'
        paper_list_bar = tqdm(soup.find_all('a'))
        paper_index = 0
        for paper in paper_list_bar:
            h3 = paper.find('h3')
            if h3 is not None:
                title = slugify(h3.text)
                paper_index += 1
            if 'download' == slugify(paper.text.strip()):
                link = paper.get('href')
                if link is not None:
                    this_paper_main_path = os.path.join(save_dir, f'{title}_{postfix}.pdf'.replace(' ', '_'))
                    paper_list_bar.set_description(f'find paper {paper_index}:{title}')
                    if not os.path.exists(this_paper_main_path) :
                        paper_list_bar.set_description(f'downloading paper {paper_index}:{title}')
                        basic_command[2] = link
                        basic_command[6] = this_paper_main_path
                        p = subprocess.Popen(' '.join(basic_command))
                        p.wait()
                        time.sleep(time_step_in_seconds)
                else:
                    error_log.append((title, 'no main link error'))
    elif year in [2009, 2008]:

        if 2009 == year:
            base_url = f'https://icml.cc/Conferences/{year}/'
            paper_list_bar = tqdm(soup.find('div', {'id': 'right_column'}).find_all(['h3','a']))
        elif 2008 == year:
            base_url = f'http://www.machinelearning.org/archive/icml{year}/'
            paper_list_bar = tqdm(soup.find('div', {'class': 'content'}).find_all(['h3','a']))
        paper_index = 0
        title = None
        for paper in paper_list_bar:
            if 'h3' == paper.name:
                title = slugify(paper.text)
                paper_index += 1
            elif 'full-paper' == slugify(paper.text.strip()):  # a
                link = paper.get('href')
                if link is not None and title is not None:
                    link = base_url + link
                    this_paper_main_path = os.path.join(save_dir, f'{title}_{postfix}.pdf')
                    paper_list_bar.set_description(f'find paper {paper_index}:{title}')
                    if not os.path.exists(this_paper_main_path):
                        paper_list_bar.set_description(f'downloading paper {paper_index}:{title}')
                        basic_command[2] = link
                        basic_command[6] = this_paper_main_path
                        p = subprocess.Popen(' '.join(basic_command))
                        p.wait()
                        time.sleep(time_step_in_seconds)
                    title = None
                else:
                    error_log.append((title, 'no main link error'))
    elif year in [2006, 2005]:
        base_url = f'https://icml.cc/Conferences/{year}/'
        paper_list_bar = tqdm(soup.find_all('a'))
        paper_index = 0
        for paper in paper_list_bar:
            title = slugify(paper.text.strip())
            link = base_url + paper.get('href')
            paper_index += 1
            if link is not None and title is not None and ('pdf' == link[-3:] or 'ps' == link[-2:]):
                this_paper_main_path = os.path.join(save_dir, f'{title}_{postfix}.pdf'.replace(' ', '_'))
                paper_list_bar.set_description(f'find paper {paper_index}:{title}')
                if not os.path.exists(this_paper_main_path):
                    paper_list_bar.set_description(f'downloading paper {paper_index}:{title}')
                    basic_command[2] = link
                    basic_command[6] = this_paper_main_path
                    p = subprocess.Popen(' '.join(basic_command))
                    p.wait()
                    time.sleep(time_step_in_seconds)
    elif 2004 == year:
        paper_index = 0
        base_url = f'https://icml.cc/Conferences/{year}/'
        paper_list_bar = tqdm(soup.find('table', {'class': 'proceedings'}).find_all('tr'))
        title = None
        for paper in paper_list_bar:
            tr_class = None
            try:
                tr_class = paper.get('class')[0]
            except:
                pass
            if 'proc_2004_title' == tr_class: # title
                title = slugify(paper.text.strip())
                paper_index += 1
            else:
                for a in paper.find_all('a'):
                    if '[Paper]' == a.text:
                        link = base_url + a.get('href')
                        if link is not None and title is not None:
                            this_paper_main_path = os.path.join(save_dir, f'{title}_{postfix}.pdf'.replace(' ', '_'))
                            paper_list_bar.set_description(f'find paper {paper_index}:{title}')
                            if not os.path.exists(this_paper_main_path):
                                paper_list_bar.set_description(f'downloading paper {paper_index}:{title}')
                                basic_command[2] = link
                                basic_command[6] = this_paper_main_path
                                p = subprocess.Popen(' '.join(basic_command))
                                p.wait()
                                time.sleep(time_step_in_seconds)
                        break
    elif 2003 == year:
        paper_index = 0
        base_url = f'https://aaai.org/'
        paper_list_bar = tqdm(soup.find('div', {'id': 'content'}).find_all('p', {'class': 'left'}))
        for paper in paper_list_bar:
            abs_link = None
            title = None
            link = None
            for a in paper.find_all('a'):
                abs_link = 'https://aaai.org/Library/ICML/' + a.get('href')
                if abs_link is not None:
                    title = slugify(a.text.strip())
                    break
            if title is not None:
                paper_index += 1
                this_paper_main_path = os.path.join(save_dir, f'{title}_{postfix}.pdf'.replace(' ', '_'))
                paper_list_bar.set_description(f'find paper {paper_index}:{title}')
                if not os.path.exists(this_paper_main_path):
                    if abs_link is not None:
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
                        req = urllib.request.Request(url=abs_link, headers=headers)
                        for i in range(3):
                            try:
                                abs_content = urllib.request.urlopen(req, timeout=10).read()
                                break
                            except Exception as e:
                                if i == 2:
                                    print('error'+title+str(e))
                                    error_log.append((title, abs_link, 'download error', str(e)))
                        abs_soup = BeautifulSoup(abs_content, 'html5lib')
                        for a in abs_soup.find_all('a'):
                            try:
                                if 'pdf' == a.get('href')[-3:]:
                                    link = base_url + a.get('href')[9:]
                                    if link is not None:
                                        paper_list_bar.set_description(f'downloading paper {paper_index}:{title}')
                                        basic_command[2] = link
                                        basic_command[6] = this_paper_main_path
                                        p = subprocess.Popen(' '.join(basic_command))
                                        p.wait()
                                        time.sleep(time_step_in_seconds)
                                    break
                            except:
                                pass

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
    error_log = []
    paper_bar = tqdm(os.scandir(main_path))
    for paper in paper_bar:
        if paper.is_file():
            name, extension = os.path.splitext(paper.name)
            if '.pdf' == extension:
                paper_bar.set_description(f'''processing {name}''')
                if os.path.exists(os.path.join(save_path, paper.name)):
                    continue
                supp_pdf_path = None
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


def rename_downloaded_paper(year, source_path):
    """
    rename the downloaded ICML paper to {title}_ICML_2010.pdf and save to source_path
    :param year: int, year
    :param source_path: str, whose structure should be source_path/papers/pdf files (2010)
                                                                  /index.html       (2010)
                                                       source_path/icml2007_proc.html (2007)
   :return:
    """
    if not os.path.exists(source_path):
        raise ValueError(f'can not find {source_path}')
    postfix = f'ICML_{year}'
    if 2010 == year:
        soup = BeautifulSoup(open(os.path.join(source_path, 'index.html'), 'rb'), 'html5lib')
        paper_list_bar = tqdm(soup.find_all('span', {'class': 'boxpopup3'}))

        for paper in paper_list_bar:
            a = paper.find('a')
            title = slugify(a.text)
            ori_name = os.path.join(source_path, 'papers', a.get('href').split('/')[-1])
            os.rename(ori_name, os.path.join(source_path, f'{title}_{postfix}.pdf'))
            paper_list_bar.set_description(f'processing {title}')
    elif 2007 == year:
        soup = BeautifulSoup(open(os.path.join(source_path, 'icml2007_proc.html'), 'rb'), 'html5lib')
        paper_list_bar = tqdm(soup.find_all('td', {'colspan': '2'}))
        for paper in paper_list_bar:
            all_as = paper.find_all('a')
            if len(all_as) <= 1:
                title = slugify(paper.text.strip())
            else:
                for a in all_as:
                    if '[Paper]' == a.text:
                        sub_path = a.get('href')
                        os.rename(os.path.join(source_path, sub_path),
                                  os.path.join(source_path, f'{title}_{postfix}.pdf'))
                        paper_list_bar.set_description_str((f'processing {title}'))
                        break


if __name__ == '__main__':
    year = 2008
    download_paper_and_sup_IDM(year, f'..\\ICML_{year}', is_download_supplement=True, time_step_in_seconds=1)
    # merge_main_supplement(main_path=f'..\\ICML_{year}\\main_paper',
    #                       supplement_path=f'..\\ICML_{year}\\supplement',
    #                       save_path=f'..\\ICML_{year}',
    #                       is_delete_ori_files=True)
    # rename_downloaded_paper(year, f'..\\ICML_{year}')
    pass