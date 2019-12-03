"""paper_download_IDM.py"""

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

# use IDM to download everything
idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"''' # should replace by the local IDM path
basic_command = [idm_path, '/d', 'xxxx', '/p', os.getcwd(), '/f', 'xxxx', '/n']
init_url = 'https://papers.nips.cc/book/advances-in-neural-information-processing-systems-32-2019'
# create current dict
title_list = []
paper_dict = dict()

paper_website = 'http://papers.nips.cc'
postfix = 'NIPS_2019'
paper_saver_path = '.\\NIPS_2019'
os.makedirs(paper_saver_path, exist_ok=True)
if os.path.exists('init_url.dat'):
    with open('init_url.dat', 'rb') as f:
        content = pickle.load(f)
else:
    content = urlopen(init_url).read()
    with open('init_url.dat', 'wb') as f:
        pickle.dump(content, f)
        
soup = BeautifulSoup(content, 'html.parser')
temp_soup = soup.find_all('ul')[1]   # after the book section
paper_list = temp_soup.find_all('li')
error_log = []
# num_download = 5 # number of papers to download
num_download = len(paper_list)

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

            
# parse each paper
index_paper = 0
for p in tqdm(zip(paper_list, range(num_download))):
    index_paper += 1
    # get title
    print('\n')
    p = p[0]
    title = p.a.text
    try:
        print(title)
    except:
        print(title.encode('utf8'))
        
    if ':' in title:
        title = title.replace(':', ' - ')
    title = "".join(i for i in title if i not in """"\/:*?<>|^{}""")
    title_list.append(title)

    try:
        asc_title = title.encode('utf-8').decode('ascii')
    except:
        print('has non english characters, canceled!')
        continue

    this_paper_path = os.path.join(paper_saver_path, f'{title}_{postfix}.pdf')
    this_paper_main_path = os.path.join(paper_saver_path, f'{title}_{postfix}_main.pdf'.replace(' ', '_'))
    this_paper_supp_path = os.path.join(paper_saver_path, f'{title}_{postfix}_supp.pdf'.replace(' ', '_'))
    this_paper_supp_path_no_ext = os.path.join(paper_saver_path, f'{title}_{postfix}_supp.'.replace(' ', '_'))

    # if index_paper < 1057:
    #     continue
    if os.path.exists(this_paper_path) and os.path.exists(this_paper_supp_path):
        os.remove(this_paper_path)
        print(f'''removed {this_paper_path}''')
    # continue

    # get abstract page url
    url2 = p.a.get('href')
    
    if os.path.exists(this_paper_path):
        continue
    # if os.path.exists(os.path.join(paper_saver_path, f'{title}_{postfix}_supp.pdf'.replace(' ', '_'))):
    #     continue

    # try 3 times
    success_flag = False
    error_flag = False
    merger_error_flag = False

    for d_iter in range(3):
        try:
            abs_content = urlopen(paper_website+url2, timeout=20).read()
            soup_temp = BeautifulSoup(abs_content, 'html.parser')
            abstract = soup_temp.find('p',{'class':'abstract'}).text.strip()
            paper_dict[title] = abstract
            
            paper_link = soup_temp.findAll('a')[4].get('href')
            supp_link = soup_temp.findAll('a')[6].get('href')
            supp_type = supp_link.split('.')[-1]
            
            # download paper with IDM

            basic_command[2] = paper_website + paper_link
            basic_command[6] = this_paper_main_path
            if not os.path.exists(this_paper_main_path):
                p = subprocess.Popen(' '.join(basic_command))
                while True:
                    if os.path.exists(this_paper_main_path):
                        break
            
            # download supp
            supp_succ_download = False
            # check whether the supp can be downloaded
            try:
                req = urlopen(paper_website + supp_link, None, 5)
                supp_succ_download = True
                no_supp = False
            except Exception as e:
                no_supp = e.code == 404            
            
            if not no_supp:
                basic_command[2] = paper_website + supp_link
                basic_command[6] = this_paper_supp_path_no_ext + supp_type

                if not (os.path.exists(this_paper_supp_path) or
                        os.path.exists(this_paper_supp_path_no_ext + supp_type)):
                    p = subprocess.Popen(' '.join(basic_command))
                    p.wait()
                    while True:
                        if os.path.exists(this_paper_supp_path_no_ext + supp_type):
                            break                
                supp_succ_download = True
                
            time.sleep(2)
            if error_flag:
                # if it is error last time download, wait 2s here
                time.sleep(2 * (d_iter + 1))
            
            if not no_supp and supp_succ_download:    
                # if zip file, unzip and extrac pdf file
                if supp_type == 'zip':
                    if not os.path.exists(this_paper_supp_path):
                        zip_ref = zipfile.ZipFile(this_paper_supp_path_no_ext + supp_type, 'r')
                        zip_ref.extractall(temp_zip_dir)
                        zip_ref.close()

                        # find if there is a pdf file (by listing all files in the dir)
                        supp_pdf_list = [os.path.join(dp, f) for dp, dn, filenames in os.walk(temp_zip_dir) for f in filenames if f.endswith('pdf')]
                        # rename the first pdf file
                        if len(supp_pdf_list) == 0:
                            supp_pdf_path = None
                        else:
                            # by default, we only deal with the first pdf
                            supp_pdf_path = this_paper_supp_path
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

                        if supp_pdf_path is None:
                            if os.path.exists(this_paper_supp_path_no_ext + supp_type):
                                os.remove(this_paper_supp_path_no_ext + supp_type)
                            if not os.path.exists(this_paper_path):
                                os.rename(this_paper_main_path, this_paper_path)
                                print('\tfinished!')
                                success_flag = True
                            break
                    else:  # have extracted pdf file from zip file before.
                        supp_pdf_path = this_paper_supp_path
                    
                elif supp_type.lower() == 'pdf':
                    supp_pdf_path = this_paper_supp_path
                    
                
                # combine two pdfs into one file
                merger_error_flag = True
                merger = PdfFileMerger()
                f_handle1 = open(this_paper_main_path, 'rb')
                merger.append(f_handle1)
                f_handle2 = open(this_paper_supp_path, 'rb')
                merger.append(f_handle2)
                    
                with open(this_paper_path, 'wb') as fout:
                    merger.write(fout)
                    print('\tmerged!')
                    
                f_handle1.close()
                f_handle2.close()
                merger.close()
                merger_error_flag = False
                success_flag = True
                # remove main.pdf and supp.pdf
                if os.path.exists(this_paper_main_path):
                    os.remove(this_paper_main_path)
                if os.path.exists(this_paper_supp_path):
                    os.remove(this_paper_supp_path)
                if os.path.exists(this_paper_supp_path_no_ext + 'zip'):
                    os.remove(this_paper_supp_path_no_ext + 'zip')

            elif no_supp:
                # rename the main.pdf with title
                os.rename(this_paper_main_path, this_paper_path)
                print('\tfinished!')
                success_flag = True
            else:
                # download supp error
                time.sleep(5)
                if os.path.exists(this_paper_supp_path):
                    os.remove(this_paper_supp_path)
                if os.path.exists(this_paper_supp_path_no_ext + supp_type):
                    os.remove(this_paper_supp_path_no_ext + supp_type)
                continue

            break
        except Exception as e:
            error_flag = True
            print('Error: ' + title + ' - ' + str(e))
            time.sleep(5)
            if merger_error_flag:
                if os.path.exists(this_paper_path):
                    os.remove(this_paper_path)
                break
            continue

    if not success_flag:
        paper_dict[title] = '\n'       
        error_log.append((title, paper_website+url2))
        print('ERROR: ' + title)

# store the results
# 1. store in the pickle file
with open(f'{postfix}_pre.dat','wb') as f:
    pickle.dump(paper_dict, f)

# 2. write error log
print('write error log')
with open('download_err_log.txt', 'w') as f:
    for log in tqdm(error_log):
        for e in log:
            f.write(e)
            f.write('\n')
    
        f.write('\n')
