"""
openreview.py
20230104
"""

import time
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import os
# https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename
from slugify import slugify
from lib.downloader import Downloader
from lib.proxy import get_proxy
import urllib
from lib.arxiv import get_pdf_link_from_arxiv


def get_driver(proxy_ip_port=None):
    # driver = webdriver.Chrome(driver_path)
    capabilities = webdriver.DesiredCapabilities.CHROME
    if proxy_ip_port is not None:
        proxy = get_proxy(proxy_ip_port)
        proxy.add_to_capabilities(capabilities)
    
    # https://stackoverflow.com/a/78797164
    chrome_install = ChromeDriverManager().install()
    folder = os.path.dirname(chrome_install)
    chromedriver_path = os.path.join(folder, "chromedriver.exe")
    driver = webdriver.Chrome(
        service=Service(executable_path=chromedriver_path),
        desired_capabilities=capabilities)
    return driver


def __download_papers_given_divs(driver, divs, save_dir, paper_postfix,
                                 time_step_in_seconds=10, downloader='IDM',
                                 proxy_ip_port=None):
    error_log = []
    downloader = Downloader(downloader=downloader, proxy_ip_port=proxy_ip_port)
    
    # scroll to top of page
    # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
    driver.find_element(By.TAG_NAME, 'body').send_keys(
        Keys.CONTROL + Keys.HOME)
    time.sleep(0.3)

    # titles = [d.text for d in divs]
    titles = []
    for d in divs:
        for i in range(3):  # temp workaround
            try:
                titles.append(d.text)    
                break
            except Exception as e:
                if i == 2:
                    print(f'\tget Exception: {str(e.msg)}')
                time.sleep(0.3)
                       
    valid_divs = []
    for i, t in enumerate(titles):
        if len(t):
            valid_divs.append(divs[i])
    num_papers = len(valid_divs)
    print('found number of papers:', num_papers)
    name = None
    for index, paper in enumerate(valid_divs):
        is_get_paper = False
        try:
            a_hrefs = paper.find_elements(By.TAG_NAME, "a")
            name = slugify(a_hrefs[0].text.strip())
            if a_hrefs[1].get_attribute('class') == 'pdf-link':
                # has pdf button
                link = a_hrefs[1].get_attribute('href')
                link = urllib.parse.urljoin('https://openreview.net', link)
            else:
                # raise ValueError('pdf link not found!')
                print('\tWarning: pdf link not found, skip this download...')
                if name is not None:
                    error_log.append((name, str(index)))
                else:
                    error_log.append((str(index), str(index)))
                continue
                # TODO: find pdf link in paper abstract page
            if name == '':
                continue
            is_get_paper = True
        except Exception as e:
            print(f'\tget Exception: {str(e.msg)}')
            print('\tskip this download...')
            if name is not None:
                error_log.append((name, str(index)))
            else:
                error_log.append((str(index), str(index)))
        if not is_get_paper:
            continue

        # name = slugify(paper.find_element_by_class_name('note_content_title').text)
        # link = paper.find_element_by_class_name('note_content_pdf').get_attribute('href')
        pdf_name = name + '_' + paper_postfix + '.pdf'
        if not os.path.exists(os.path.join(save_dir, pdf_name)):
            print('Downloading paper {}/{}: {}'.format(index + 1, num_papers,
                                                       name))
            # get pdf link of arxiv if the original link is on arxiv.org
            if "arxiv.org/abs" in link:
                link = get_pdf_link_from_arxiv(abs_link=link)
            # try 1 times
            success_flag = False
            for d_iter in range(1):
                try:
                    downloader.download(
                        urls=link,
                        save_path=os.path.join(save_dir, pdf_name),
                        time_sleep_in_seconds=time_step_in_seconds
                    )
                    success_flag = True
                    break
                except Exception as e:
                    print('Error: ' + name + ' - ' + str(e))
            if not success_flag:
                error_log.append((name, link))
    return error_log, num_papers


def __get_into_pages_given_number(driver, page_number, pages, wait_fn,
                                  condition=None):
    wait_fn(driver, condition)
    for page in pages:
        if page.text.isnumeric() and int(page.text) == page_number:
            page_link = page.find_element(By.TAG_NAME, "a")
            page_link.click()
            wait_fn(driver, condition)
            return page

    return None


def download_nips_papers_given_url(
        save_dir, year, base_url, conference='NIPS', start_page=1,
        time_step_in_seconds=10, download_groups='all', downloader='IDM',
        proxy_ip_port=None):
    """
    download NeurIPS papers from the given web url.
    :param save_dir: str, paper save path
    :type save_dir: str
    :param year: int, iclr year, current only support year >= 2018
    :type year: int
    :param base_url: str, paper website url
    :type base_url: str
    :param conference: str, conference name, such as NIPS.
    :param start_page: int, the initial downloading webpage number, only the pages whose number is
                            equal to or greater than this number will be processed.
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :param groups: group name, such as 'oral', 'spotlight', 'poster'.
        Default: 'all'.
    :type download_groups: str | list[str]
    :param downloader: str, the downloader to download, could be 'IDM' or None,
        default to 'IDM'
    :param proxy_ip_port: str or None, proxy server ip address with or without
        protocol prefix, eg: "127.0.0.1:7890", "http://127.0.0.1:7890".
        (only useful for None|"request" downloader and webdriver)
        Default: None
    :return:
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if year < 2023:
        sub_xpath = '''id="accepted-papers"'''
    else:
        sub_xpath = '''class="submissions-list"'''
    def mywait(driver, condition=None):
        # wait for the select element to become visible
        # print('Starting web driver wait...')
        # ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        # wait = WebDriverWait(driver, 20, ignored_exceptions=ignored_exceptions)
        wait = WebDriverWait(driver, 20)
        # print('Starting web driver wait... finished')
        # res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
        # print("Successful load the website!->", res)
        # res = wait.until(
        #     EC.presence_of_element_located((By.CLASS_NAME, "note")))
        res = wait.until(
            EC.presence_of_element_located((By.ID, "notes")))
        # print("Successful load the website notes!->", res)
        res = wait.until(EC.presence_of_element_located(
            (By.XPATH, f'''//*[@{sub_xpath}]/nav''')))
        # print("Successful load the website pagination!->", res)
        time.sleep(2)  # seconds, workaround for bugs

    def find_divs_of_papers():
        if year < 2023:
            divs = driver.find_element(By.ID, group_id). \
                find_elements(By.CLASS_NAME, 'note ')
        else:
            # divs = driver.find_element(By.ID, group_id). \
            #     find_elements(By.XPATH, '//*[@class="note  undefined"]')
            divs = driver.find_element(By.ID, group_id).find_elements(
                By.XPATH, 
                '//*[contains(@class, "note") and contains(@class, "undefined")]'
            )
        return divs

    paper_postfix = f'{conference}_{year}'
    error_log = []
    driver = get_driver(proxy_ip_port=proxy_ip_port)
    driver.get(base_url)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    mywait(driver)
    # pages = driver.find_elements_by_xpath('//*[@id="accepted-papers"]/nav/ul/li')

    # download grouped papers, such as "Accepted Papaers" for year before 2023
    # "Accept (oral)", "Accept (spotlight)", "Accept (poster)" for year 2023
    groups = driver.find_elements(
        By.XPATH, f'//*[@id="notes"]/div/div[1]/ul/li')
    accept_groups = []
    for g in groups:
        if 'accept' in g.text.lower():
            # whether download this group
            is_download_group = True
            if not 'all' == download_groups:
                is_download_group = False
                for dg in download_groups:
                    if dg.lower() in g.text.lower():
                        is_download_group = True
                        break
            if is_download_group:
                accept_groups.append(g)
    group_name = None
    group_save_dir = save_dir
    for ag in accept_groups:
        group_name = slugify(ag.text)
        group_save_dir = os.path.join(save_dir, group_name)
        print(f'Downloading {group_name}...')
        os.makedirs(group_save_dir, exist_ok=True)
        number_paper_group = 0
        accept_group_link = ag.find_element(By.TAG_NAME, "a")
        group_id = accept_group_link.get_attribute('aria-controls')
        # scroll to top of page, if not at top, the click action not work
        # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
        driver.find_element(By.TAG_NAME, 'body').send_keys(
            Keys.CONTROL + Keys.HOME)
        time.sleep(0.2)
        accept_group_link.click()
        mywait(driver)
        pages = driver.find_elements(
            By.XPATH, f'//*[@{sub_xpath}]/nav[1]/ul/li')
        page_str_list = get_pages_str(pages)
        # print(f'Current page navigation bar:\n{page_str_list}')
        current_page = 1
        ind_page = 2  # 0 << ; 1 <
        # << | < | 1, 2, 3, ... | > | >>
        total_pages_number = get_max_page_number(page_str_list)
        last_total_pages = total_pages_number
        # get into start pages
        while current_page < start_page:
            if total_pages_number < start_page:  # flip pages until seeing the start page
                current_page = total_pages_number
                __get_into_pages_given_number(
                    driver=driver, page_number=current_page, pages=pages,
                    wait_fn=mywait)
                print(f'getting into web page {current_page}...')
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, '//*[@id="accepted-papers"]/ul/li/h4/a')))
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, '''//*[@id="accepted-papers"]/nav''')))
                mywait(driver)

                # print("Successful load the website pagination!->", res)
                # pages = driver.find_elements_by_xpath('//*[@id="accepted-papers"]/nav/ul/li')
                pages = pages = driver.find_elements(
                    By.XPATH, f'//*[@{sub_xpath}]/nav[1]/ul/li')
                page_str_list = get_pages_str(pages)
                total_pages_number = get_max_page_number(page_str_list)
                # # print(f'Current page navigation bar:\n{page_str_list}')
                if total_pages_number == last_total_pages:  # total page remain unchanged after reload
                    print(f'reached last({total_pages_number}-th) webpage')
                    # when get the last page, but the page number is till less than start page, so
                    # the start page doesn't exist. PRINT ERROR and return
                    print(f'ERROR: THE {start_page}-th webpage not found!')
                    return
            else:
                current_page = start_page

        page = __get_into_pages_given_number(
            driver=driver, page_number=current_page, pages=pages,
            wait_fn=mywait)

        while current_page <= total_pages_number:
            if page is None:
                break
            print(f'downloading papers in page: {current_page}')
            mywait(driver)

            # divs = driver.find_elements_by_xpath('//*[@id="accepted-papers"]/ul/li')
            # divs = driver.find_elements(By.XPATH, '//*[@id="accepted-papers"]/ul/li')
            divs = find_divs_of_papers()

            # temp workaround
            repeat_times = 3
            is_find_paper = False
            for r in range(repeat_times):
                try:
                    a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    is_find_paper = True
                    break
                except Exception as e:
                    if (r + 1) < repeat_times:
                        print(f'\terror occurre: {str(e)}')
                        print(f'\tsleep {(r + 1) * 5} seconds...')
                        time.sleep((r + 1) * 5)
                        print(f'{r + 1}-th reloading page')
                        divs = find_divs_of_papers()
                    else:
                        print('\tskip this page.')
            if not is_find_paper:
                continue

            # time.sleep(time_step_in_seconds)
            this_error_log, this_number_paper = __download_papers_given_divs(
                driver=driver,
                divs=divs,
                save_dir=group_save_dir,
                paper_postfix=paper_postfix,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                proxy_ip_port=proxy_ip_port
            )
            for e in this_error_log:
                error_log.append(e)
            number_paper_group += this_number_paper
            # get into next page
            current_page += 1
            # pages = driver.find_elements_by_xpath('//*[@id="accepted-papers"]/nav/ul/li')
            pages = driver.find_elements(
                By.XPATH, f'//*[@{sub_xpath}]/nav[1]/ul/li')
            page_str_list = get_pages_str(pages)
            total_pages_number = get_max_page_number(page_str_list)
            # print(f'Current page navigation bar:\n{page_str_list}')
            # if we do not reread the pages, all the pages will be not available with an exception:
            # selenium.common.exceptions.StaleElementReferenceException:
            # Message: stale element reference: element is not attached to the page document
            page = __get_into_pages_given_number(driver=driver,
                                                 page_number=current_page,
                                                 pages=pages,
                                                 wait_fn=mywait)
        # display total number of papers
        print(f'number of papers in {group_name}: {number_paper_group}')

    driver.quit()
    # 2. write error log
    print('write error log')
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'download_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                f.write(e)
                f.write('\n')
            f.write('\n')


def download_iclr_papers_given_url_and_group_id(
        save_dir, year, base_url, group_id, conference='ICLR', start_page=1,
        time_step_in_seconds=10, downloader='IDM', proxy_ip_port=None,
        is_have_pages=True, is_need_click_group_button=False):
    """
    downlaod ICLR papers for the given web url and the paper group id
    :param save_dir: str, paper save path
    :type save_dir: str
    :param year: int, iclr year, current only support year >= 2018
    :type year: int
    :param base_url: str, paper website url
    :type base_url: str
    :param group_id: str, paper group id, such as "notable-top-5-",
        "notable-top-25-", "poster", "oral-submissions",
        "spotlight-submissions", "poster-submissions", etc.
    :type group_id: str
    :param conference: str, conference name, such as ICLR. Default: ICLR
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Default: 1
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds. Default: 10
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder'. Default: 'IDM'
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890".  Only useful for webdriver and request
        downloader (downloader=None). Default: None.
    :type proxy_ip_port: str | None
    :param is_have_pages: bool, is there pages in webpage. Default:
        True.
    :type is_have_pages: bool
    :param is_need_click_group_button: bool, is there need to click the
        group button in webpage. For some years, for example 2018, the
        navigation part "#xxxxx" in base url will not work. And it should
        be clicked before reading content from webpage. Default: False.
    :type is_need_click_group_button: bool
    :return:
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    def _get_pages_xpath(year):
        if year <= 2023:
            xpath = f'''//*[@id="{group_id}"]/nav/ul/li'''
        else:
            xpath = f'''//*[@id="{group_id}"]/div/div/nav/ul/li'''
        return xpath

    def mywait(driver, condition=None):
        # wait for the select element to become visible
        # print('Starting web driver wait...')
        # ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        # wait = WebDriverWait(driver, 20, ignored_exceptions=ignored_exceptions)
        wait = WebDriverWait(driver, 20)
        # print('Starting web driver wait... finished')
        # res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
        # print("Successful load the website!->", res)
        if year <= 2023:
            res = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "note")))
        # print("Successful load the website notes!->", res)
        # res = wait.until(EC.presence_of_element_located(
        #     (By.XPATH, f'''//*[@id="{group_id}"]/nav''')))
        if is_have_pages:
            # scroll to bottom of page
            # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
            driver.find_element(By.TAG_NAME, 'body').send_keys(
                Keys.CONTROL + Keys.END)
            if year <= 2023:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f'{_get_pages_xpath(year)}[3]/a')))
            else:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f'{_get_pages_xpath(year)}[3]/a')))
            # print("Successful load the website pagination!->", res)
        time.sleep(2)  # seconds, workaround for bugs

    paper_postfix = f'{conference}_{year}'
    error_log = []
    driver = get_driver(proxy_ip_port=proxy_ip_port)
    driver.get(base_url)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if is_need_click_group_button:
        archive_is_have_pages = is_have_pages
        is_have_pages = False
        mywait(driver)
        aria_controls = base_url.split('#')[-1]
        # scroll to home of page
        driver.find_element(By.TAG_NAME, 'body').send_keys(
            Keys.CONTROL + Keys.HOME)
        group_button = driver.find_element(
            By.XPATH, f"""//a[@aria-controls="{aria_controls}"]"""
        )
        group_button.click()
        is_have_pages = archive_is_have_pages
    mywait(driver)
    if is_have_pages:
        pages = driver.find_elements(By.XPATH, _get_pages_xpath(year))
        current_page = 1
        ind_page = 2  # 0 << ; 1 <
        total_pages_number = int(pages[-3].text)
        # << | < | 1, 2, 3, ... | > | >>
        last_total_pages = total_pages_number
        # get into start pages
        while current_page < start_page:
            # flip pages until seeing the start page
            if total_pages_number < start_page:
                current_page = total_pages_number
                __get_into_pages_given_number(
                    driver=driver, page_number=current_page, pages=pages,
                    wait_fn=mywait)
                print(f'getting into web page {current_page}...')
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, f'//*[@id="{group_id}"]/ul/li/h4/a')))
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, f'''//*[@id="{group_id}"]/nav''')))
                mywait(driver)

                # print("Successful load the website pagination!->", res)
                pages = driver.find_elements(
                    By.XPATH, _get_pages_xpath(year))
                total_pages_number = int(pages[-3].text)
                # total page remain unchanged after reload
                if total_pages_number == last_total_pages:
                    print(f'reached last({total_pages_number}-th) webpage')
                    # when get the last page, but the page number is till
                    # less than start page, so the start page doesn't exist.
                    # PRINT ERROR and return
                    print(f'ERROR: THE {start_page}-th webpage not found!')
                    return
            else:
                current_page = start_page

        page = __get_into_pages_given_number(
            driver=driver, page_number=current_page, pages=pages, wait_fn=mywait)

        while current_page <= total_pages_number:
            if page is None:
                break
            print(f'downloading {group_id} papers in page: {current_page}')
            mywait(driver)

            divs = driver.find_element(By.ID, group_id). \
                find_elements(By.CLASS_NAME, 'note ')

            # temp workaround
            repeat_times = 3
            is_find_paper = False
            for r in range(repeat_times):
                try:
                    a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    is_find_paper = True
                    break
                except Exception as e:
                    if (r + 1) < repeat_times:
                        print(f'\terror occurre: {str(e.msg)}')
                        print(f'\tsleep {(r + 1) * 5} seconds...')
                        time.sleep((r + 1) * 5)
                        print(f'{r + 1}-th reloading page')
                        divs = driver.find_element(By.ID, group_id). \
                            find_elements(By.CLASS_NAME, 'note ')
                    else:
                        print('\tskip this page.')
            if not is_find_paper:
                continue

            # time.sleep(time_step_in_seconds)
            this_error_log, this_number_paper = __download_papers_given_divs(
                driver=driver,
                divs=divs,
                save_dir=save_dir,
                paper_postfix=paper_postfix,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                proxy_ip_port=proxy_ip_port
            )
            for e in this_error_log:
                error_log.append(e)
            # get into next page
            current_page += 1
            pages = driver.find_elements(
                By.XPATH, _get_pages_xpath(year))
            total_pages_number = int(pages[-3].text)
            # if we do not reread the pages, all the pages will be not available
            # with an exception:
            # selenium.common.exceptions.StaleElementReferenceException:
            # Message: stale element reference: element is not attached to the
            # page document
            page = __get_into_pages_given_number(
                driver=driver, page_number=current_page, pages=pages,
                wait_fn=mywait)
    else:  # no pages
        divs = driver.find_element(By.ID, group_id). \
            find_elements(By.CLASS_NAME, 'note ')
        # temp workaround
        repeat_times = 3
        is_find_paper = False
        for r in range(repeat_times):
            try:
                a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                is_find_paper = True
                break
            except Exception as e:
                if (r + 1) < repeat_times:
                    print(f'\terror occurre: {str(e.msg)}')
                    print(f'\tsleep {(r + 1) * 5} seconds...')
                    time.sleep((r + 1) * 5)
                    print(f'{r + 1}-th reloading page')
                    divs = driver.find_element(By.ID, group_id). \
                        find_elements(By.CLASS_NAME, 'note ')
                else:
                    print('\tskipped!!!')
        if is_find_paper:
            # time.sleep(time_step_in_seconds)
            this_error_log, this_number_paper = __download_papers_given_divs(
                driver=driver,
                divs=divs,
                save_dir=save_dir,
                paper_postfix=paper_postfix,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                proxy_ip_port=proxy_ip_port
            )
            for e in this_error_log:
                error_log.append(e)

    driver.quit()
    # 2. write error log
    print('write error log')
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'download_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                f.write(e)
                f.write('\n')
            f.write('\n')


def download_icml_papers_given_url_and_group_id(
        save_dir, year, base_url, group_id, conference='ICML', start_page=1,
        time_step_in_seconds=10, downloader='IDM', proxy_ip_port=None):
    """
    downlaod ICLR papers for the given web url and the paper group id
    :param save_dir: str, paper save path
    :type save_dir: str
    :param year: int, iclr year, current only support year >= 2018
    :type year: int
    :param base_url: str, paper website url
    :type base_url: str
    :param group_id: str, paper group id, such as "poster" and "oral".
    :type group_id: str
    :param conference: str, conference name, such as ICLR. Default: ICLR
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Default: 1
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds. Default: 10
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder'. Default: 'IDM'
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Only useful for webdriver and request
        downloader (downloader=None). Default: None.
    :type proxy_ip_port: str | None
    :return:
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    def mywait(driver, aria_controls=None):
        # wait for the select element to become visible
        # print('Starting web driver wait...')
        wait = WebDriverWait(driver, 20)
        # ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        # wait = WebDriverWait(driver, 20, ignored_exceptions=ignored_exceptions)
        # print('Starting web driver wait... finished')
        # res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
        # print("Successful load the website!->", res)
        res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
        res = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "submissions-list")))
        # print("Successful load the website notes!->", res)
        # res = wait.until(EC.presence_of_element_located(
        #     (By.XPATH, f'''//*[@id="{group_id}"]/nav''')))
        # scroll to bottom of page
        # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
        driver.find_element(By.TAG_NAME, 'body').send_keys(
            Keys.CONTROL + Keys.END)
        time.sleep(0.3)
        if aria_controls is None:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, f'//*[@class="submissions-list"]/nav/ul/li[3]/a''')))
        else:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH,
                 f'''//*[@id='{aria_controls}']/div/div/nav/ul/li[3]/a''')))
            wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 f'''//*[@id='{aria_controls}']/div/div/ul/li[1]/div/h4/a[1]''')))
        # print("Successful load the website pagination!->", res)
        time.sleep(2)  # seconds, workaround for bugs

    paper_postfix = f'{conference}_{year}'
    error_log = []
    driver = get_driver(proxy_ip_port=proxy_ip_port)
    driver.get(base_url)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # wait = WebDriverWait(driver, 20)
    mywait(driver)

    # get into poster or oral page
    nav_tap = driver.find_elements(
        By.XPATH, f'//ul[@class="nav nav-tabs"]/li')
    is_found_group = False
    for li in nav_tap:
        if group_id in li.text.lower():
            if 'poster' in group_id and 'spotlight' in li.text.lower():
                # spotlight-poster should be recognized as spotlight rather
                # than poster
                continue
            page_link = li.find_element(By.TAG_NAME, "a")
            # scroll to top of page, if not at top, the click action not work
            # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
            driver.find_element(By.TAG_NAME, 'body').send_keys(
                Keys.CONTROL + Keys.HOME)
            aria_controls = page_link.get_attribute('aria-controls')
            page_link.click()
            mywait(driver, aria_controls)  # there is no request in here
            is_found_group = True
            break
    if not is_found_group:
        raise ValueError(f'not found {group_id} papers at {base_url}!!!')

    # pages = driver.find_elements(
    #     By.XPATH, f'//nav[@aria-label="page navigation"]/ul/li')
    pages = driver.find_elements(
        By.XPATH, f'''//*[@id='{aria_controls}']/div/div/nav/ul/li''')
    current_page = 1
    # ind_page = 2  # 0 << ; 1 <
    total_pages_number = int(pages[-3].text)  # << | < | 1, 2, 3, ... | > | >>
    last_total_pages = total_pages_number
    # get into start pages
    while current_page < start_page:
        # flip pages until seeing the start page
        if total_pages_number < start_page:
            current_page = total_pages_number
            __get_into_pages_given_number(
                driver=driver, page_number=current_page, pages=pages,
                wait_fn=mywait, condition=aria_controls)
            print(f'getting into web page {current_page}...')

            # print("Successful load the website pagination!->", res)
            pages = driver.find_elements(
                By.XPATH, f'''//*[@id='{aria_controls}']/div/div/nav/ul/li''')
            total_pages_number = int(pages[-3].text)
            # total page remain unchanged after reload
            if total_pages_number == last_total_pages:
                print(f'reached last({total_pages_number}-th) webpage')
                # when get the last page, but the page number is till less than
                # start page, so the start page doesn't exist. PRINT ERROR and
                # return
                print(f'ERROR: THE {start_page}-th webpage not found!')
                return
        else:
            current_page = start_page

    page = __get_into_pages_given_number(
        driver=driver, page_number=current_page, pages=pages, wait_fn=mywait,
        condition=aria_controls)

    while current_page <= total_pages_number:
        if page is None:
            break
        print(f'downloading {group_id} papers in page: {current_page}')

        divs = driver.find_elements(
            By.XPATH, f'''//*[@id='{aria_controls}']/div/div/ul/li''')

        # temp workaround
        repeat_times = 3
        is_find_paper = False
        for r in range(repeat_times):
            try:
                a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                is_find_paper = True
                break
            except Exception as e:
                if (r+1) < repeat_times:
                    print(f'\terror occurre: {str(e.msg)}')
                    print(f'\tsleep {(r+1)*5} seconds...')
                    time.sleep((r+1)*5)
                    print(f'{r+1}-th reloading page')
                    divs = driver.find_elements(
                        By.XPATH,
                        f'''//*[@id='{aria_controls}']/div/div/ul/li''')
                else:
                    print('\tskip this page.')
        if not is_find_paper:
            continue
        # time.sleep(time_step_in_seconds)
        this_error_log, this_number_paper = __download_papers_given_divs(
            driver=driver,
            divs=divs,
            save_dir=save_dir,
            paper_postfix=paper_postfix,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            proxy_ip_port=proxy_ip_port
        )
        for e in this_error_log:
            error_log.append(e)
        # get into next page
        current_page += 1
        pages = driver.find_elements(
            By.XPATH, f'''//*[@id='{aria_controls}']/div/div/nav/ul/li''')
        total_pages_number = int(pages[-3].text)
        # if we do not reread the pages, all the pages will be not available
        # with an exception:
        # selenium.common.exceptions.StaleElementReferenceException:
        # Message: stale element reference: element is not attached to the
        # page document
        page = __get_into_pages_given_number(
            driver=driver, page_number=current_page, pages=pages,
            wait_fn=mywait, condition=aria_controls)

    driver.quit()
    # 2. write error log
    print('write error log')
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'download_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                f.write(e)
                f.write('\n')
            f.write('\n')


def get_pages_str(pages):
    page_str_list = [p.text for p in pages]
    # print(f'Current page navigation bar:\n{page_str_list}')
    return page_str_list


def get_max_page_number(page_str_list):
    is_find_number = False
    for i, page_str in enumerate(page_str_list):
        if not page_str.isnumeric() and is_find_number:
            return int(page_str_list[i-1])
        if page_str.isnumeric():
            is_find_number = True
    return int(page_str_list[-1])


def download_papers_given_url_and_group_id(
        save_dir, year, base_url, group_id, conference, start_page=1,
        time_step_in_seconds=10, downloader='IDM', proxy_ip_port=None,
        is_have_pages=True, is_need_click_group_button=False):
    """
    downlaod papers for the given web url and the paper group id
    :param save_dir: str, paper save path
    :type save_dir: str
    :param year: int, iclr year, current only support year >= 2018
    :type year: int
    :param base_url: str, paper website url
    :type base_url: str
    :param group_id: str, paper group id, such as "notable-top-5-",
        "notable-top-25-", "poster", "oral-submissions",
        "spotlight-submissions", "poster-submissions", etc.
    :type group_id: str
    :param conference: str, conference name, such as CORL.
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Default: 1
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds. Default: 10
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder'. Default: 'IDM'
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890".  Only useful for webdriver and request
        downloader (downloader=None). Default: None.
    :type proxy_ip_port: str | None
    :param is_have_pages: bool, is there pages in webpage. Default:
        True.
    :type is_have_pages: bool
    :param is_need_click_group_button: bool, is there need to click the
        group button in webpage. For some years, for example 2018, the
        navigation part "#xxxxx" in base url will not work. And it should
        be clicked before reading content from webpage. Default: False.
    :type is_need_click_group_button: bool
    :return:
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    def _get_pages_xpath(year):
        if year <= 2023:
            xpath = f'''//*[@id="{group_id}"]/nav/ul/li'''
        else:
            xpath = f'''//*[@id="{group_id}"]/div/div/nav/ul/li'''
        return xpath

    def mywait(driver, condition=None):
        # wait for the select element to become visible
        # print('Starting web driver wait...')
        # ignored_exceptions = (NoSuchElementException, 
        # StaleElementReferenceException,)
        # wait = WebDriverWait(driver, 20, ignored_exceptions=ignored_exceptions)
        wait = WebDriverWait(driver, 20)
        # print('Starting web driver wait... finished')
        # res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
        # print("Successful load the website!->", res)
        # if year <= 2023:
        #     res = wait.until(
        #         EC.presence_of_element_located((By.CLASS_NAME, "note")))
        # print("Successful load the website notes!->", res)
        # res = wait.until(EC.presence_of_element_located(
        #     (By.XPATH, f'''//*[@id="{group_id}"]/nav''')))
        if is_have_pages:
            # scroll to bottom of page
            # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
            driver.find_element(By.TAG_NAME, 'body').send_keys(
                Keys.CONTROL + Keys.END)
            if year <= 2023:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f'{_get_pages_xpath(year)}[3]/a')))
            else:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f'{_get_pages_xpath(year)}[3]/a')))
            # print("Successful load the website pagination!->", res)
        time.sleep(2)  # seconds, workaround for bugs

    paper_postfix = f'{conference}_{year}'
    error_log = []
    
    driver = get_driver(proxy_ip_port=proxy_ip_port)
    driver.get(base_url)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if is_need_click_group_button:
        archive_is_have_pages = is_have_pages
        is_have_pages = False
        mywait(driver)
        aria_controls = base_url.split('#')[-1]
        # scroll to home of page
        driver.find_element(By.TAG_NAME, 'body').send_keys(
            Keys.CONTROL + Keys.HOME)
        group_button = driver.find_element(
            By.XPATH, f"""//a[@aria-controls="{aria_controls}"]"""
        )
        group_button.click()
        is_have_pages = archive_is_have_pages
    mywait(driver)
    if is_have_pages:
        pages = driver.find_elements(By.XPATH, _get_pages_xpath(year))
        current_page = 1
        ind_page = 2  # 0 << ; 1 <
        total_pages_number = int(pages[-3].text)
        # << | < | 1, 2, 3, ... | > | >>
        last_total_pages = total_pages_number
        # get into start pages
        while current_page < start_page:
            # flip pages until seeing the start page
            if total_pages_number < start_page:
                current_page = total_pages_number
                __get_into_pages_given_number(
                    driver=driver, page_number=current_page, pages=pages,
                    wait_fn=mywait)
                print(f'getting into web page {current_page}...')
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, f'//*[@id="{group_id}"]/ul/li/h4/a')))
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, f'''//*[@id="{group_id}"]/nav''')))
                mywait(driver)

                # print("Successful load the website pagination!->", res)
                pages = driver.find_elements(
                    By.XPATH, _get_pages_xpath(year))
                total_pages_number = int(pages[-3].text)
                # total page remain unchanged after reload
                if total_pages_number == last_total_pages:
                    print(f'reached last({total_pages_number}-th) webpage')
                    # when get the last page, but the page number is till
                    # less than start page, so the start page doesn't exist.
                    # PRINT ERROR and return
                    print(f'ERROR: THE {start_page}-th webpage not found!')
                    return
            else:
                current_page = start_page

        page = __get_into_pages_given_number(
            driver=driver, page_number=current_page, pages=pages, wait_fn=mywait)

        while current_page <= total_pages_number:
            if page is None:
                break
            print(f'downloading {group_id} papers in page: {current_page}')
            mywait(driver)

            divs = driver.find_element(By.ID, group_id). \
                find_elements(By.CLASS_NAME, 'note ')

            # temp workaround
            repeat_times = 3
            is_find_paper = False
            for r in range(repeat_times):
                try:
                    a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    is_find_paper = True
                    break
                except Exception as e:
                    if (r + 1) < repeat_times:
                        print(f'\terror occurre: {str(e.msg)}')
                        print(f'\tsleep {(r + 1) * 5} seconds...')
                        time.sleep((r + 1) * 5)
                        print(f'{r + 1}-th reloading page')
                        divs = driver.find_element(By.ID, group_id). \
                            find_elements(By.CLASS_NAME, 'note ')
                    else:
                        print('\tskip this page.')
            if not is_find_paper:
                continue

            # time.sleep(time_step_in_seconds)
            this_error_log, this_number_paper = __download_papers_given_divs(
                driver=driver,
                divs=divs,
                save_dir=save_dir,
                paper_postfix=paper_postfix,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                proxy_ip_port=proxy_ip_port
            )
            for e in this_error_log:
                error_log.append(e)
            # get into next page
            current_page += 1
            pages = driver.find_elements(
                By.XPATH, _get_pages_xpath(year))
            total_pages_number = int(pages[-3].text)
            # if we do not reread the pages, all the pages will be not available
            # with an exception:
            # selenium.common.exceptions.StaleElementReferenceException:
            # Message: stale element reference: element is not attached to the
            # page document
            page = __get_into_pages_given_number(
                driver=driver, page_number=current_page, pages=pages,
                wait_fn=mywait)
    else:  # no pages
        divs = driver.find_element(By.ID, group_id). \
            find_elements(By.CLASS_NAME, 'note ')
        # temp workaround
        repeat_times = 3
        is_find_paper = False
        for r in range(repeat_times):
            try:
                a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                is_find_paper = True
                break
            except Exception as e:
                if (r + 1) < repeat_times:
                    print(f'\terror occurre: {str(e.msg)}')
                    print(f'\tsleep {(r + 1) * 5} seconds...')
                    time.sleep((r + 1) * 5)
                    print(f'{r + 1}-th reloading page')
                    divs = driver.find_element(By.ID, group_id). \
                        find_elements(By.CLASS_NAME, 'note ')
                else:
                    print('\tskipped!!!')
        if is_find_paper:
            # time.sleep(time_step_in_seconds)
            this_error_log, this_number_paper = __download_papers_given_divs(
                driver=driver,
                divs=divs,
                save_dir=save_dir,
                paper_postfix=paper_postfix,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                proxy_ip_port=proxy_ip_port
            )
            for e in this_error_log:
                error_log.append(e)

    driver.quit()
    # 2. write error log
    print('write error log')
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'download_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                f.write(e)
                f.write('\n')
            f.write('\n')



if __name__ == "__main__":
    year = 2023
    save_dir = rf'E:\ICML_{year}'
    base_url = 'https://openreview.net/group?id=ICML.cc/2023/Conference'
    # download_nips_papers_given_url(
    #     save_dir, year, base_url,
    #     start_page=1,
    #     time_step_in_seconds=10,
    #     downloader='IDM')
    # download_icml_papers_given_url_and_group_id(
    #     save_dir, year, base_url, group_id='oral', start_page=1,
    #     time_step_in_seconds=10, )
