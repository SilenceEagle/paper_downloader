"""
cvf.py
20210617
"""

import urllib
from bs4 import BeautifulSoup
from tqdm import tqdm
from slugify import slugify
from .my_request import urlopen_with_retry


def get_paper_dict_list(url=None, content=None, group_name=None, timeout=10):
    """
    parse papers' title, link, supp link from content, and save in a list contains dictionaries with key "title",
        "main link", "supplemental link" and "group"(optional, if group_name is not None),
    :param url: str or None, url
    :param content: None of object return by urlopen
    :param group_name: str or None, the group name of the papers in given content
    :param timeout: int, the timeout value for open url, default to 10
    :return: paper_dict_list, list of dictionaries, that contains the dictionaries of papers with key "title",
        "main link",  "supplemental link" and "group"(optional, if group_name is not None)
        content, object return by urlopen
    """
    if url is None and content is None:
        raise ValueError('''one of "url" and "content" should be provide!!!''')
    paper_dict_list = []
    paper_dict = {'title': '', 'main link': '', 'supplemental link': '', 'arxiv': ''} if group_name is None else \
        {'group': group_name, 'title': '', 'main link': '', 'supplemental link': '', 'arxiv': ''}

    if content is None:
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
        content = urlopen_with_retry(url=url, headers=headers)
    soup = BeautifulSoup(content, 'html5lib')
    paper_list_bar = tqdm(soup.find('div', {'id': 'content'}).find_all(['dd', 'dt']))
    paper_index = 0
    for paper in paper_list_bar:
        is_new_paper = False

        # get title
        try:
            if 'dt' == paper.name and 'ptitle' == paper.get('class')[0]:  # title:
                title = slugify(paper.text.strip())
                paper_dict['title'] = title
                paper_index += 1
                paper_list_bar.set_description_str(f'Collecting paper {paper_index}: {title}')
            elif 'dd' == paper.name:
                all_as = paper.find_all('a')
                for a in all_as:
                    if 'pdf' == slugify(a.text.strip()):
                        main_link = urllib.parse.urljoin(url, a.get('href'))
                        paper_dict['main link'] = main_link
                        is_new_paper = True
                    elif 'supp' == slugify(a.text.strip()):
                        supp_link = urllib.parse.urljoin(url, a.get('href'))
                        paper_dict['supplemental link'] = supp_link
                    elif 'arxiv' == slugify(a.text.strip()):
                        arxiv = urllib.parse.urljoin(url, a.get('href'))
                        paper_dict['arxiv'] = arxiv
                        break
        except Exception as e:
            print(f'Warning: {str(e)}')

        if is_new_paper:
            paper_dict_list.append(paper_dict.copy())
            paper_dict['title'] = ''
            paper_dict['main link'] = ''
            paper_dict['supplemental link'] = ''
            paper_dict['arxiv'] = ''

    return paper_dict_list, content


