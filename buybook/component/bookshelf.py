from requests import Request, Session, PreparedRequest

import pandas as pd
from bs4 import BeautifulSoup
import logging
from buybook.component import curl_converter

logger = logging.getLogger(__name__)

class Basebookshelf(object):
    def __init__(self, session: Session):
        self.wanted_books: pd.DataFrame = None
        self.url_auth = None
        self.url_bookshelf = None
        self.s = session

    def authenticate(self) -> bool:
        (h, b, ct) = curl_converter.load()
        req:Request= None
        if ct.startswith("multipart/form-data"):
            h = curl_converter.insensitive_del(h, "content-type")
            req = Request('POST', self.url_auth, headers= h, files=b)
        elif ct.startswith("application/x-www-form-urlencoded"):
            req = Request('POST', self.url_auth, headers=h, data=b)

        prepared = req.prepare()
        res = self.s.send(prepared)
        # logger.info("Login status={0:d}".format(res.status_code))
        # logger.info("resp content={:s}".format(res.text))
        if (res.text.find('"status":"error"') >=0)  or (res.status_code != 200) :
            # readmoo, {"status":"error","desc":"","title":"error_unknown","message":[""]}
            logger.error("Status Code={:d}, Reason={:s}".format(res.status_code, res.text))
            return False
        else:
            return True

    def get_wanted_books(self):
        raise NotImplementedError("Method: " + Basebookshelf.get_wanted_books.__name__ + " not implemented")


class Readmooshare_bookself(Basebookshelf):
    def __init__(self, session):
        Basebookshelf.__init__(self, session)
        self.url_auth = "https://member.readmoo.com/login"
        self.url_bookshelf = "https://share.readmoo.com/me/bookshelf/total"

    def get_wanted_books(self):
        res= self.s.post(self.url_bookshelf)
        soup = BeautifulSoup(res.text, "lxml")
        tags = soup.find_all("li", class_="listGrids-box")
        logger.debug("Total {:d} tags found".format(len(tags)))

        data=[]
        for tag in tags:
            try:
                status = tag.select_one("a[class='btn def-to-read'] > span").string
                if (status == "想讀"):
                    caption = tag.select_one("div[class='caption'] > h5 > a")
                    title = caption["title"]
                    blink = caption["href"]
                    detail_page = self.s.get(blink).text
                    isbn = BeautifulSoup(detail_page, "lxml").select_one("span[itemprop='ISBN']").string

                    logger.info("Collecting {:s} {:s} {:s}".format(blink,title,isbn))
                    data.append([blink,title,isbn])
                    # logger.info("Collecting {0:s} --{1:s}".format(title, np.datetime64("now")))
            except Exception as e:
                logger.error(str(e))
                pass

        self.wanted_books = pd.DataFrame(data, columns=["blink","title", "isbn"])
        logger.info("Total {:d} books found".format(self.wanted_books.shape[0]))
        logger.info(self.wanted_books.to_string())
        return self.wanted_books