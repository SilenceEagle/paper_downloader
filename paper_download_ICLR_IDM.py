"""paper_download_ICLR_IDM.py"""

import time
from tqdm import tqdm
import subprocess
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
#https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename
from slugify import slugify
from bs4 import BeautifulSoup
import pickle
from urllib.request import urlopen


def download_iclr_oral_papers(save_dir, driver_path, year, base_url=None):
    if base_url is None:
        if year == 2017:
            base_url = 'https://openreview.net/group?id=ICLR.cc/2017/conference'
        elif year == 2018:
            base_url = 'https://openreview.net/group?id=ICLR.cc/2018/Conference#accepted-oral-papers'
        elif year == 2019:
            base_url = 'https://openreview.net/group?id=ICLR.cc/2019/Conference#accepted-oral-papers'
        elif year == 2020:
            base_url = 'https://openreview.net/group?id=ICLR.cc/2020/Conference#accept-talk'
        else:
            raise ValueError('the website url is not given for this year!')
    first_poster_index = {'2017': 15}
    paper_postfix = f'ICLR_{year}'
    error_log = []
    driver = webdriver.Chrome(driver_path)
    driver.get(base_url)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # wait for the select element to become visible
    print('Starting web driver wait...')
    wait = WebDriverWait(driver, 20)
    print('Starting web driver wait... finished')
    res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
    print("Successful load the website!->",res)
    res = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "note")))
    print("Successful load the website notes!->",res)
    # parse the results

    if year >= 2020:
        divs = driver.find_elements_by_xpath('//*[@id="accept-talk"]/ul/li')
    elif year >= 2018:
        divs = driver.find_elements_by_xpath('//*[@id="accepted-poster-papers"]/ul/li')
    else:
        divs = driver.find_elements_by_class_name('note')[:first_poster_index[str(year)]]
    num_papers = len(divs)
    print('found number of papers:',num_papers)
    for index, paper in enumerate(divs):
        a_hrefs = paper.find_elements_by_tag_name("a")
        if year >= 2018:
            name = slugify(a_hrefs[0].text.strip())
            link = a_hrefs[1].get_attribute('href')
        else:
            name = slugify(paper.find_element_by_class_name('note_content_title').text)
            link = paper.find_element_by_class_name('note_content_pdf').get_attribute('href')
        print('Downloading paper {}/{}: {}'.format(index+1, num_papers, name))
        pdf_name = name + '_' + paper_postfix + '.pdf'
        if not os.path.exists(os.path.join(save_dir, pdf_name)):
            # try 1 times
            success_flag = False
            for d_iter in range(1):
                try:
                    download_pdf_idm(link, os.path.join(save_dir, pdf_name))
                    time.sleep(5)
                    success_flag = True
                    break
                except Exception as e:
                    print('Error: ' + name + ' - ' + str(e))
                    time.sleep(5)
            if not success_flag:
                error_log.append((name, link))
    driver.close()
    # 2. write error log
    print('write error log')
    with open(os.path.join(save_dir, 'download_err_log.txt'), 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                f.write(e)
                f.write('\n')
            f.write('\n')


def download_iclr_poster_papers(save_dir, driver_path, year, base_url=None):
    if base_url is None:
        if year == 2017:
            base_url = 'https://openreview.net/group?id=ICLR.cc/2017/conference'
        elif year == 2018:
            base_url = 'https://openreview.net/group?id=ICLR.cc/2018/Conference#accepted-poster-papers'
        elif year == 2019:
            base_url = 'https://openreview.net/group?id=ICLR.cc/2019/Conference#accepted-poster-papers'
        elif year == 2020:
            base_url = 'https://openreview.net/group?id=ICLR.cc/2020/Conference#accept-poster'
        else:
            raise ValueError('the website url is not given for this year!')
    first_poster_index={'2017': 15}
    first_workshop_title = {'2017': 'Learning Continuous Semantic Representations of Symbolic Expressions'}
    paper_postfix = f'ICLR_{year}'
    error_log = []
    driver = webdriver.Chrome(driver_path)
    driver.get(base_url)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # wait for the select element to become visible
    print('Starting web driver wait...')
    wait = WebDriverWait(driver, 20)
    print('Starting web driver wait... finished')
    res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
    print("Successful load the website!->",res)
    res = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "note")))
    print("Successful load the website notes!->",res)
    # parse the results
    if year >= 2020:
        divs = driver.find_elements_by_xpath('//*[@id="accept-poster"]/ul/li')
    elif year >= 2018:
        divs = driver.find_elements_by_xpath('//*[@id="accepted-poster-papers"]/ul/li')
    else:
        divs = driver.find_elements_by_class_name('note')[first_poster_index[str(year)]:]
    num_papers = len(divs)
    print('found number of papers:',num_papers)
    for index, paper in enumerate(divs):
        a_hrefs = paper.find_elements_by_tag_name("a")
        if year >= 2018:
            name = slugify(a_hrefs[0].text.strip())
            link = a_hrefs[1].get_attribute('href')
        else:
            name = slugify(paper.find_element_by_class_name('note_content_title').text)
            link = paper.find_element_by_class_name('note_content_pdf').get_attribute('href')
            if name == slugify(first_workshop_title[str(year)]):  # all the poster paper has been downloaded
                break
        print('Downloading paper {}/{}: {}'.format(index+1, num_papers, name))
        pdf_name = name + '_' + paper_postfix + '.pdf'
        if not os.path.exists(os.path.join(save_dir, pdf_name)):
            # try 1 times
            success_flag = False
            for d_iter in range(1):
                try:
                    download_pdf_idm(link, os.path.join(save_dir, pdf_name))
                    time.sleep(5)
                    success_flag = True
                    break
                except Exception as e:
                    print('Error: ' + name + ' - ' + str(e))
                    time.sleep(5)
            if not success_flag:
                error_log.append((name, link))
    driver.close()
    # 2. write error log
    print('write error log')
    with open(os.path.join(save_dir, 'download_err_log.txt'), 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                f.write(e)
                f.write('\n')
            f.write('\n')


def download_iclr_paper(year, save_dir):
    """
    download iclr conference paper for year 2014, 2015 and 2016
    :param year: int, iclr year
    :param save_dir: str, paper save path
    :return: True
    """
    is_use_arxiv_mirror = True
    paper_postfix = f'ICLR_{year}'
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
        os.makedirs(oral_save_path, exist_ok=True)
        os.makedirs(poster_save_path, exist_ok=True)
    if os.path.exists(f'init_url_iclr_{year}.dat'):
        with open(f'init_url_iclr_{year}.dat', 'rb') as f:
            content = pickle.load(f)
    else:
        content = urlopen(base_url).read()
        with open(f'init_url_iclr_{year}.dat', 'wb') as f:
            pickle.dump(content, f)
    error_log = []
    soup = BeautifulSoup(content, 'html.parser')
    print('open url successfully!')
    if year == 2016:
        papers = soup.find('h3', {'id': 'accepted_papers_conference_track'}).findNext('div').find_all('a')
        for paper in tqdm(papers):
            link = paper.get('href')
            if link.startswith('http://arxiv'):
                title = slugify(paper.text)
                try:
                    if not os.path.exists(os.path.join(save_dir, title+f'_{paper_postfix}.pdf')):
                        pdf_link = get_pdf_link_from_arxiv(link, is_use_mirror=is_use_arxiv_mirror)
                        print(f'downloading {title}')
                        download_pdf_idm(pdf_link, os.path.join(save_dir, title+f'_{paper_postfix}.pdf'))
                        time.sleep(5)
                except Exception as e:
                    # error_flag = True
                    print('Error: ' + title + ' - ' + str(e))
                    error_log.append((title, link, 'paper download error', str(e)))
    elif year == 2015:
        # oral papers
        oral_papers = soup.find('h3', {'id': 'conference_oral_presentations'}).findNext('div').find_all('a')
        for paper in tqdm(oral_papers):
            link = paper.get('href')
            if link.startswith('http://arxiv'):
                title = slugify(paper.text)
                try:
                    if not os.path.exists(os.path.join(oral_save_path, title+f'_{paper_postfix}.pdf')):
                        pdf_link = get_pdf_link_from_arxiv(link, is_use_mirror=is_use_arxiv_mirror)
                        print(f'downloading {title}')
                        download_pdf_idm(pdf_link, os.path.join(oral_save_path, title+f'_{paper_postfix}.pdf'))
                        time.sleep(5)
                except Exception as e:
                    # error_flag = True
                    print('Error: ' + title + ' - ' + str(e))
                    error_log.append((title, link, 'paper download error', str(e)))

        # poster papers
        poster_papers = soup.find('h3', {'id': 'may_9_conference_poster_session'}).findNext('div').find_all('a')
        for paper in tqdm(poster_papers):
            link = paper.get('href')
            if link.startswith('http://arxiv'):
                title = slugify(paper.text)
                try:
                    if not os.path.exists(os.path.join(poster_save_path, title + f'_{paper_postfix}.pdf')):
                        pdf_link = get_pdf_link_from_arxiv(link, is_use_mirror=is_use_arxiv_mirror)
                        print(f'downloading {title}')
                        download_pdf_idm(pdf_link, os.path.join(poster_save_path, title + f'_{paper_postfix}.pdf'))
                        time.sleep(5)
                except Exception as e:
                    # error_flag = True
                    print('Error: ' + title + ' - ' + str(e))
                    error_log.append((title, link, 'paper download error', str(e)))
    elif year == 2014:
        papers = soup.find('div', {'id': 'sites-canvas-main-content'}).find_all('a')
        for paper in tqdm(papers):
            link = paper.get('href')
            if link.startswith('http://arxiv'):
                title = slugify(paper.text)
                try:
                    if not os.path.exists(os.path.join(save_dir, title + f'_{paper_postfix}.pdf')):
                        pdf_link = get_pdf_link_from_arxiv(link, is_use_mirror=is_use_arxiv_mirror)
                        print(f'downloading {title}')
                        download_pdf_idm(pdf_link, os.path.join(save_dir, title + f'_{paper_postfix}.pdf'))
                        time.sleep(5)
                except Exception as e:
                    # error_flag = True
                    print('Error: ' + title + ' - ' + str(e))
                    error_log.append((title, link, 'paper download error', str(e)))


    # write error log
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
    return True


def get_pdf_link_from_arxiv(abs_link, is_use_mirror=True):
    if is_use_mirror:
        # abs_link = abs_link.replace('arxiv.org', 'xxx.itp.ac.cn')
        abs_link = abs_link.replace('arxiv.org', 'cn.arxiv.org')
        for i in range(3):  # try 3 times
            try:
                abs_content = urlopen(abs_link, timeout=20).read()
                break
            except:
                if 2 == i:
                    return None
        abs_soup = BeautifulSoup(abs_content, 'html.parser')
        pdf_link = 'http://cn.arxiv.org' + abs_soup.find('div', {'class': 'full-text'}).find('ul').find('a').get('href')
    else:
        for i in range(3):  # try 3 times
            try:
                abs_content = urlopen(abs_link, timeout=20).read()
                break
            except:
                if 2 == i:
                    return None
        abs_soup = BeautifulSoup(abs_content, 'html.parser')
        pdf_link = 'http://arxiv.org' + abs_soup.find('div', {'class': 'full-text'}).find('ul').find('a').get('href')
        if pdf_link[-3:] != 'pdf':
            pdf_link += '.pdf'
    return pdf_link

def download_pdf(url, name):
    r = requests.get(url, stream=True)

    with open('%s.pdf' % name, 'wb') as f:
        for chunck in r.iter_content(1024):
            f.write(chunck)
    r.close()


def download_pdf_idm(url, name):
    # use IDM to download everything
    idm_path = '''"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'''  # should replace by the local IDM path
    basic_command = [idm_path, '/d', 'xxxx', '/p', os.getcwd(), '/f', 'xxxx', '/n']
    basic_command[2] = url
    basic_command[6] = name
    if os.path.exists(name):
        return
    p = subprocess.Popen(' '.join(basic_command))
    p.wait()
    # while True:
    #     if os.path.exists(name):
    #         break
    return


if __name__ == '__main__':
    year = 2014
    # driver_path = r'c:\files\chromedriver.exe'
    # save_dir_iclr = f'.\\ICLR_{year}_poster'

    # download_iclr_oral_papers(save_dir_iclr, driver_path, year)
    # download_iclr_poster_papers(save_dir_iclr, driver_path, year)
    download_iclr_paper(year, save_dir=f'..\\ICLR_{year}')


