from typing import NamedTuple, List, Dict, Union, Hashable, Any
import pandas as pd
import requests
import logging
from datetime import datetime
import yaml
from booksearch import Basebooksearch
from bookshelf import Readmooshare_bookself

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
                    )
logger = logging.getLogger(__name__)

class QbookConfig():
    def __init__(self, config:Dict = None) -> None:
        super().__init__()
        if config is not None:
            self.config: Dict[Hashable, Any] = config

    def load(self,  fname="buybook.yaml"):
        with open(fname, "r", encoding="UTF-8") as f:
            self.config: Dict[Hashable, Any] = yaml.load(f)

        # self.shelfConfig: Dict[Hashable, Any] = self.config["shelf"]
        self.searchConfig:Dict[Hashable, Any] = self.config["search"]

config:QbookConfig = QbookConfig()
config.load(".\qbook.yaml")

class QBook(NamedTuple):
    wanted_books:pd.DataFrame
    booksearch:List[Basebooksearch]

    # r: each row
    def highlight_book(self, r) -> bool:
        return True if r["searching"] in r["title"] else False

    # r: each row
    def color_book(self, r) -> List[str]:
            return ['background-color: yellow' if r["searching"] in r["title"] else '' for v in r]

    def to_wishlist(self) -> pd.DataFrame:
        # merge search results
        wishlist = self.booksearch[0].search(self.wanted_books)
        for bs in self.booksearch[1:]:
            rs = bs.search(self.wanted_books)
            wishlist = pd.merge(wishlist, rs, how="outer")

        # add a column indicating the possible search matches & remove irrelevant rows which is False in highlight column
        wishlist["highlight"] = wishlist.apply(self.highlight_book, axis=1)
        wishlist = wishlist[wishlist["highlight"] == True]


        # sory by price
        wishlist = wishlist.sort_values(by=["searching", "title", "price"])
        # logger.debug(wishlist.to_string())

        return wishlist
