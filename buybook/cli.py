import pandas as pd
from tabulate import tabulate

from buybook.component.booksearch import Basebooksearch
from buybook.component.qbook import QBook, QbookConfig

config:QbookConfig = QbookConfig()
config.load()

if __name__ == "__main__":
    # q = input("Book title?")
    q= "搖擺時代"
    if q is not None:
        wanted_books = pd.DataFrame({"title":[q], "blink":["N/A"], "isbn":["N/A"]})
        bsearch = [Basebooksearch(k, config.searchConfig[k]) for k in config.searchConfig.keys()]
        qb = QBook(wanted_books= wanted_books, booksearch=bsearch)
        wishlist = qb.to_wishlist()
        wishlist.drop(["searching", "blink", "desc", "highlight"], axis="columns", inplace=True)
        print(tabulate(wishlist, headers = "keys", tablefmt='presto', showindex=False))

