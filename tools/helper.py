def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def yaml_read(path):
    import yaml
    yml = dict()
    with open(path, 'r') as stream:
        try:
            yml = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return yml


def remove_html_tags(text):
    from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
    import warnings
    import re
    warnings.filterwarnings('ignore', category=MarkupResemblesLocatorWarning)
    
    soup = BeautifulSoup(text, features="lxml")
    text = soup.text
    text = re.sub(r"\s+", " ", text)
    text = re.sub("\n", "", text)
    for link in soup.find_all('a'):
        text = text + " " + link.get('href') if link.get('href') else text
    return text
