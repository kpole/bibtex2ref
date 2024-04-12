# -*- coding: utf-8 -*-
# ---------------------
# requirement:
# pip install requests
# pip install beautifulsoup4
# pip install lxml
# pip install --no-cache-dir --force-reinstall git+https://github.com/sciunto-org/python-bibtexparser@main 

import requests
from bs4 import BeautifulSoup
import bibtexparser
from bibtexparser.middlewares import BlockMiddleware
import bibtexparser.middlewares as m
import re
import termcolor

# 自定义 name merge 中间件
class MergeNameParts(BlockMiddleware):
    def transform_entry(self, entry, *args, **kwargs):
        MAX_AUTHOR_COUNT = 6
        convert_names = []
        for name_part in entry['author'][:MAX_AUTHOR_COUNT]:
            convert_names.append(' '.join([*name_part.first, *name_part.last]))
        
        if len(entry['author']) > MAX_AUTHOR_COUNT:
            convert_names.append("et al")
        entry['author'] = ', '.join(convert_names)
        return entry

def modify_book_title(entry, key):
    booktitle = []
    entry[key] = re.sub(r'\s+', ' ', entry[key])
    for item in entry[key].replace("\n", "").split(','):
        item = item.replace('{', '')
        item = item.replace('}', '')
        item = item.strip()
        booktitle.append(item)
    print(booktitle)
    entry[key] = ', '.join(booktitle)

def get_bibtex_from_dblp():
    BASE_URL = "https://dblp.uni-trier.de"

    paper_name = input("Please input the paper name: ")
    url = f"{BASE_URL}/search/publ/inc?q={paper_name}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    # Find all <li> elements with class 'entry'
    entries = soup.find_all('li', class_='entry')

    if len(entries) == 0:
        print(termcolor.colored("Nothing found", "yellow"))

    # Extract and print the 'id' attribute of each entry
    entry_ids = []
    for (index, entry) in enumerate(entries):
        entry_id = entry.get('id')
        entry_ids.append(entry_id)
        title_span = entry.find('span', class_='title')
        author_names = list(entry.find_all('span', attrs={"itemprop": "author"}))
        o = termcolor.colored(f'[{index}]: ', 'blue')
        o += f"\t {','.join([author.text for author in author_names[:3]])}...\n"
        o += termcolor.colored(f"\t {title_span.text}", 'green')
        print(o)

    select_id = int(input(f"Please input your selection (in [{0}-{len(entry_ids) - 1}] ): "))

    while select_id < 0 or select_id >= len(entry_ids):
        select_id = int(input(f"Please re-enter your selection (in [{0}-{len(entry_ids) - 1}] ): "))

    entry_ids = entry_ids[select_id]

    bibtex_url = BASE_URL + f"/rec/{entry_id}.html/?view=bibtex" 
    response = requests.get(bibtex_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        bibtex_content = soup.find('pre', class_='verbatim')
        bibtex_content = bibtex_content.text
    return bibtex_content

def get_bibtex_from_input():
    ret = ""
    print("Please enter content in bibtex format, ending with a separate end:")
    while True:
        line = input()
        if line == "end":
            break
        ret += line
    print(ret)
    return ret

def parse_bibtex(bibtex_content):
    bib_database = bibtexparser.parse_string(bibtex_content)

    entry_dict = bib_database.entries[0]
    print(termcolor.colored("Entry Content:", "blue"))
    print(entry_dict)

    layers = [
        m.SeparateCoAuthors(),
        m.SplitNameParts(),
        MergeNameParts(),
    ]
    library = bibtexparser.parse_string(bibtex_content, append_middleware=layers)
    entry = library.entries[0]

    entry['title'] = re.sub(r'\s+', ' ', entry['title'])
    ref_content = ""
    try:
        if 'booktitle' in entry:
            modify_book_title(entry, 'booktitle')
            ref_content = entry['author'] + ". " + entry['title'] + ". " + "In: " + entry['booktitle'] + ": " + entry['pages']
        else:
            if 'number' not in entry:
                entry['number'] = '[number]'
            if 'pages' not in entry:
                entry['pages'] = '[pages]'
            if 'volume' not in entry:
                entry['volume'] = '[volume]'
            if 'journal' not in entry:
                entry['journal'] = '[journal]'
            if entry['journal'][-1] == '.':
                entry['journal'] = entry['journal'][:-1]
            modify_book_title(entry, 'journal')
            ref_content = entry['author'] + ". " + entry['title'] + ". " + entry['journal'] + ", " + entry['year'] + ", " + entry['volume'] + f"({entry['number']})" + ": " + entry['pages']

        print(termcolor.colored("Ref:", "light_blue"))
        print(termcolor.colored(ref_content, "green"))
    except Exception as e:
        print(e)
        print("格式解析错误")

def main():
    opt = int(input("1. Search from above dblp.\n2. Manually enter bibtex\nPlease select a method: "))
    while opt != 1 and opt != 2:
        opt = int(input("Please reselect a method: "))
    if opt == 1:
        bibtex_content = get_bibtex_from_dblp()
    else:
        bibtex_content = get_bibtex_from_input()

    parse_bibtex(bibtex_content)

if __name__ == '__main__':
    main()