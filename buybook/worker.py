import logging
from typing import Union
import pandas as pd
import pika
import os
import sys
import requests

from buybook.component.booksearch import Basebooksearch
from buybook.component.bookshelf import Readmooshare_bookself
from buybook.component.qbook import QbookConfig, QBook

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
                    )

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', '5672')
RABBITMQ_ROUTINGKEY = os.environ.get('RABBITMQ_ROUTINGKEY', 'buybook_search')
credentials = pika.PlainCredentials(os.environ.get('RABBITMQ_USER', 'guest'), os.environ.get('RABBITMQ_PASSWORD', 'guest'))
RABBITMQ_HEATBEAT = os.environ.get('RABBITMQ_HEATBEAT', 600)
RABBITMQ_BLOCKED_CONNECTION_TIMEOUT = os.environ.get('RABBITMQ_BLOCKED_CONNECTION_TIMEOUT', 300)

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials,
                                                               heartbeat=RABBITMQ_HEATBEAT, blocked_connection_timeout=RABBITMQ_BLOCKED_CONNECTION_TIMEOUT))
channel = connection.channel()
channel.queue_declare(queue=RABBITMQ_ROUTINGKEY)

config:QbookConfig = QbookConfig()
config.load()
bsearch = [Basebooksearch(k, config.searchConfig[k]) for k in config.searchConfig.keys()]

logger = logging.getLogger(__name__)


def get_mybookshelf() -> pd.DataFrame:
    with requests.Session() as s:
        bs = Readmooshare_bookself(session=s)
        is_auth = bs.authenticate()
        logger.debug(f"Bookshelf authentication is {is_auth}")
        if is_auth:
            return bs.get_wanted_books()
        else:
            return None


def search_book(q:Union[str, pd.DataFrame]):
    # wanted_books = pd.DataFrame({"title": [q], "blink": ["N/A"], "isbn": ["N/A"]})

    wanted_books = pd.DataFrame({"title": [q], "blink": ["N/A"], "isbn": ["N/A"]}) if isinstance(q, str) else q
    qb = QBook(wanted_books=wanted_books, booksearch=bsearch)
    wishlist = qb.to_wishlist()
    # wishlist.drop(["searching", "blink", "desc", "highlight"], axis="columns", inplace=True)
    wishlist.drop(["searching", "highlight"], axis="columns", inplace=True)
    return wishlist.to_json(orient="records")


def receive():
    def callback(ch, method, props, body):
        q = str(body, encoding="utf-8")
        if q.lower() == "mybookshelf":
            q = get_mybookshelf()

        if q is not None:
            logger.info(f" [3] Starting search {q}")
            response = search_book(q)
        else:
            logger.error(" [-1] Either q is None or MyBookself login failure...")
            response = "Either q is None or MyBookself login failure..."

        logger.info(f" [4] Receive result and send to Callback{props.correlation_id}")
        channel.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=bytes(response, "utf-8"))

        # ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=RABBITMQ_ROUTINGKEY, on_message_callback=callback, auto_ack=True)
    logger.info(' [0] Waiting for messages')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        receive()
    except KeyboardInterrupt:
        logger.error('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)