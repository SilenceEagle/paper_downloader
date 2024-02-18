"""
arxiv.py
20240218
"""
from bs4 import BeautifulSoup
from urllib.request import urlopen

def get_pdf_link_from_arxiv(abs_link, is_use_mirror=False):
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
        pdf_link = 'http://cn.arxiv.org' + abs_soup.find('div', {
            'class': 'full-text'}).find('ul').find('a').get('href')
    else:
        for i in range(3):  # try 3 times
            try:
                abs_content = urlopen(abs_link, timeout=20).read()
                break
            except:
                if 2 == i:
                    return None
        abs_soup = BeautifulSoup(abs_content, 'html.parser')
        pdf_link = 'http://arxiv.org' + abs_soup.find('div', {
            'class': 'full-text'}).find('ul').find('a').get('href')
        if pdf_link[-3:] != 'pdf':
            pdf_link += '.pdf'
    return pdf_link
