"""
ACM.py
some functions of acm
20200817
"""
import urllib
from urllib.request import urlopen, Request
import time
import bs4
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def get_pdf_link_given_acm_abs_url(abs_url, driver_path=r'c:\chromedriver.exe'):
    try:
        # r = Request(abs_url, headers={'User-Agent': 'Mozilla/5.0'})
        # content = urlopen(r).read()
        # soup = BeautifulSoup(content, 'html5lib')
        # pdf_a = soup.find('a', {'title': 'PDF'})
        # pdf_link = pdf_a.get('href')
        # pdf_link = urllib.parse.urljoin(abs_url, pdf_link)
        driver = webdriver.Chrome(driver_path)
        driver.get(abs_url)
        driver.implicitly_wait(10)  # seconds

        # # wait for the select element to become visible
        # print('Starting web driver wait...')
        # wait = WebDriverWait(driver, 20)
        # print('Starting web driver wait... finished')
        # res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
        # print("Successful load the website!->", res)
        # res = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "note")))
        # print("Successful load the website notes!->", res)
        # parse the results
        pdf_a = driver.find_elements_by_xpath('//*[@title="PDF"]')
        pdf_link = pdf_a[0].get_attribute('href')
        pdf_link = urllib.parse.urljoin(abs_url, pdf_link)
        driver.close()
    except Exception as e:
        print(str(e))
        return ''

    return pdf_link


if __name__ == '__main__':
    abs_url = 'https://dl.acm.org/doi/10.1145/3354918.3361903'
    driver_path = r'c:\chromedriver.exe'
    get_pdf_link_given_acm_abs_url(abs_url, driver_path)