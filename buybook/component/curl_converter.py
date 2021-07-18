import logging
import os
from typing import List, Tuple, Dict
import re


logger = logging.getLogger(__name__)

def load(fname:str="cURL.bash") -> Tuple[dict, dict, str]:
    d = os.path.dirname(__file__)
    fname = os.path.join(d, fname)
    logger.debug(f"cURL loading {fname}")
    with open(fname, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return convert(lines)

def convert(lines) -> Tuple[dict, dict, str]:
    header_lines = []
    body_line: str = ""
    content_type: str = ""

    for line in lines:
        line = line.strip()
        if line.startswith("-H"):
            line = get_quote_str(line)
            if line.lower().startswith("content-type"):
                content_type = to_kv(line)[1]
            header_lines.append(line)
        elif line.startswith("--data-raw"):
            body_line = get_quote_str(line)

    headers = get_headers(header_lines)
    body = get_body(body_line, content_type)
    return (headers, body, content_type)


def get_headers(s: List[str]) -> Dict:
    l = []

    for line in s:
        (k, v) = to_kv(line)
        l.append((k, v))

    return combine_kv(l)


def get_body(s: str, ct: str) -> Dict:
    l = []
    if ct.startswith("application/x-www-form-urlencoded"):
        l = get_application_x_www_form_urlencoded_body(s)
    elif ct.startswith("multipart/form-data"):
        l = get_multipart_form_data_body(s, ct)

    return combine_kv(l)


def get_multipart_form_data_body(s: str, ct: str) -> List[Tuple]:
    '''
        file = {'k1': (None, '12345'), 'k2': (None, '67890')})
    :param s:
    :param ct:
    :return:
    '''

    list: List[Tuple] = []
    b = ct.split("WebKitFormBoundary")[1]
    pattern = r'------WebKitFormBoundary{:s}\\r\\nContent-Disposition: form-data; name="(.+?)"\\r\\n\\r\\n(.+?)\\r\\n'.format(b)
    zz = re.findall(pattern, s)
    for (k, v) in zz:
        # k = r"------WebKitFormBoundary{:s}\r\nContent-Disposition: form-data; name={:s}".format(b, k)
        # list.append((k, v))
        list.append((k, (None, v)))
    return list


def get_application_x_www_form_urlencoded_body(s: str) -> List[Tuple]:
    '''
        data = {"param1": "value1", "param2": "value2"}
    '''
    list: List[Tuple] = []
    pattern = r"(.+?)=(.+?)&"
    zz = re.findall(pattern, s)
    for (k, v) in zz:
        list.append((k, v))
    return list


def get_application_json_body(s: str) -> List[Tuple]:
    pass



def to_kv(s: str, separator=":") -> Tuple[str, str]:
    idx = s.index(separator)
    return (s[:idx].strip(), s[idx+1:].strip())


def combine_kv(l: List[Tuple]) -> Dict:
    '''
    [('a',1),('b', 2), ('c', 3)] =>  {'a': 1, 'b': 2, 'c': 3}
    :param l: list of tuple
    :return: dict
    '''
    zipped = list(zip(*l))
    d = dict(zip(*zipped))
    return d

def insensitive_del(d:Dict, target:str) -> Dict:
    for k in d.keys():
        if k.lower == target.lower():
            del d[k]
    return d

def get_quote_str(l: str, quote="'") -> str:
    '''
    "abc*defgh*ikg*"  -> "defgh"
    :param l: input str w quote
    :param quote: quote
    :return: sub str within quote
    '''
    return l.split(quote, 2)[1]




if __name__ == "__main__":
    fname = "C:\\Users\Flyhead\\Desktop\\new 3.TXT"
    with open(fname, "r", encoding="utf-8") as f:
        lines = f.readlines()

    (h, b, ct) = convert(lines)
    print(h)
    print(b)
