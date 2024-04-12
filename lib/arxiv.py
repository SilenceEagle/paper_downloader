"""
arxiv.py
20240218
"""
from bs4 import BeautifulSoup
from .my_request import urlopen_with_retry

def get_pdf_link_from_arxiv(abs_link, is_use_mirror=False):
    headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) '
            'Gecko/20100101 Firefox/23.0'}
    mirror = 'cn.arxiv.org'
    if is_use_mirror:
        abs_link = abs_link.replace('arxiv.org', mirror)

    abs_content = urlopen_with_retry(
        url=abs_link, headers=headers, raise_error_if_failed=False)
    if abs_content is None:
        return None
    abs_soup = BeautifulSoup(abs_content, 'html.parser')
    pdf_link = 'http://arxiv.org' + abs_soup.find('div', {
        'class': 'full-text'}).find('ul').find('a').get('href')
    if pdf_link[-3:] != 'pdf':
        pdf_link += '.pdf'
    if is_use_mirror:
        pdf_link = pdf_link.replace('arxiv.org', mirror)
    return pdf_link
