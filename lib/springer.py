"""
springer.py
some function for springer
20201106
"""

import urllib
from bs4 import BeautifulSoup
from tqdm import tqdm
from slugify import slugify
from .my_request import urlopen_with_retry
import re


def get_paper_name_link_from_url(url):
    headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
    paper_dict = dict()
    content = urlopen_with_retry(url=url, headers=headers)
    soup = BeautifulSoup(content, 'html5lib')
    paper_list_bar = tqdm(
        soup.find('section', {'data-title': 'Table of contents'}).find(
            'div', {'class': 'c-book-section'}).find_all(
            ['li'], {'data-test': 'chapter'}))
    for paper in paper_list_bar:
        try:
            title = slugify(
                paper.find(['h3', 'h4'], {'class': 'app-card-open__heading'}).text)
            link = urllib.parse.urljoin(
                url, 
                paper.find(
                    ['h3', 'h4'], {'class': 'app-card-open__heading'}
                    ).a.get('href'))
            # 'https://link.springer.com/chapter/10.1007/978-3-642-33718-5_2' 
            # >>
            # 'https://link.springer.com/content/pdf/10.1007/978-3-642-33718-5_2.pdf'
            link = f'''{link.replace('/chapter/', '/content/pdf/')}.pdf'''
            paper_dict[title] = link
        except Exception as e:
            print(f'ERROR: {str(e)}')
    return paper_dict




if __name__ == '__main__':
    papers = get_paper_name_link_from_url('https://link.springer.com/book/10.1007%2F978-3-319-46448-0')