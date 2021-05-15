from typing import Dict, Hashable, Any

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import logging
import re
from structure import Params,  Book

logger = logging.getLogger(__name__)
pattern = re.compile(r"\((.+)\)")

class Basebooksearch(object):
    def __init__(self, source: str, config:Dict[Hashable, Any]):
        self.search_result:pd.DataFrame = None
        self.source = source
        self.query= config["query"]
        self.book= config["book"]

    def parse_book(self, r, tag):
        l = list()
        l.append(self.source)
        l.append(r["title"]) # searching kw

        book = Book(self.book, tag)
        l.append(book.get_info("title"))
        l.append(book.get_info("blink"))
        l.append(self.strip_desc(book.get_info("desc")))
        l.append( self.clean_price(book.get_info("price")))
        return l

    def strip_desc(self, t:str) ->str:
        '''
        remove multiple space within description
        :param t: book description with multiple space
        :return: book description w/o multiple space
        '''
        t1= " ".join(t.strip().split())
        return t1[0:100]

    # def remove_dollor_sign(self, p:str) ->int:
    #     return int(p.replace("$", ""))

    def clean_price(self, price_text:str) -> int:
        '''
        remove $ from the price text and convert to NTD
        :param t: price text
        :return: price
        '''

        # Kobo
        price_text1 = price_text.replace("NT$", "")
        # Google
        price_text2 = price_text1.replace("$", "")

        try:
            price = 0 if price_text2 == "免費" else round(float(price_text2))
        except Exception:
            logger.error("price_text ={:s} {:s} {:s}".format(price_text, price_text1, price_text2))
            return 0
        return price



    def search(self, wanted_books:pd.DataFrame) -> pd.DataFrame:
        data = list()
        for index, r in wanted_books.iterrows():
            with requests.session() as s:

                p = Params(self.query["params"], r)
                res = s.get(url=self.query["url"], headers={"accept-language":"zh-TW"},  params=p.get_transformeddict())
                res.raise_for_status()

                soup = BeautifulSoup(res.text, "lxml")
                tags = soup.select(self.book["booklist"]["selector"])
                # logger.info("Searching {:s},{:d} books found,{:s}".format(r["title"], len(tags), np.datetime64("now")))
                logger.info("{:s} is searching {:s},{:d} books found".format(self.source, r["title"], len(tags), ))

                # Only previous 10 book at most to save time
                for tag in tags[:10]:
                    try:
                        logger.debug(" ".join(tag.get_text().split()))
                        l = self.parse_book(r, tag)
                        data.append(l)
                    except Exception as e:
                        logger.error(str(e))
                        pass


        self.search_result = pd.DataFrame(data, columns=["source", "searching", "title", "blink", "desc", "price"])
        logger.debug((self.search_result.to_string()))
        return self.search_result



if __name__ == "__main__":
    bs = Basebooksearch()

