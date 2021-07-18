import requests
import logging
from datetime import datetime

from buybook.component.booksearch import Basebooksearch
from buybook.component.bookshelf import Readmooshare_bookself
from buybook.component.qbook import QbookConfig, QBook

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
                    )
logger = logging.getLogger(__name__)

config:QbookConfig = QbookConfig()
config.load(".\qbook.yaml")


def main():
    # config:QbookConfig = QbookConfig()
    # config.load(".\buybook.yaml")

    with requests.Session() as s:
        bs = Readmooshare_bookself(s)
        if bs.authenticate():
            wanted_books = bs.get_wanted_books()
            no_of_wanted_books = len(wanted_books)
            logger.info("Wanted book {:d} found!".format(no_of_wanted_books))

            if no_of_wanted_books > 0:
                bsearch = [ Basebooksearch(k, config.searchConfig[k]) for k in config.searchConfig.keys() ]

                # TESTING!!!
                qb = QBook(wanted_books= wanted_books[0:5], booksearch=bsearch)
                wishlist = qb.to_wishlist()

                # write to csv
                wishlist.to_csv("wishlist-" + datetime.now().strftime("%Y%m%d%H%M%S") + ".csv",
                                columns=["source", "searching", "title", "price", "desc", "blink"])

                # write to html
                # pass each row to color_book(), note the return must match the shape of row
                # with open(os.path.join(boring_stuff.DATA_DIR, "bookshelf/wishlist_" +boring_stuff.TIMESTAMP1 +".html"), "w+", encoding="utf8") as f:
                #     f.write(wishlist.style.set_properties(**{'max-width': '200px',  'border-color': 'black', 'font-size': '16pt'}).apply(color_book, axis=1).render())


if __name__ == "__main__":

    main()
