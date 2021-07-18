import json
import logging
import os
import uuid
from typing import Hashable, Dict, Any, Union, AnyStr
import pika
from flask import Flask, render_template

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', '5672')
RABBITMQ_ROUTINGKEY = os.environ.get('RABBITMQ_ROUTINGKEY', 'buybook_search')
credentials = pika.PlainCredentials(os.environ.get('RABBITMQ_USER', 'guest'), os.environ.get('RABBITMQ_PASSWORD', 'guest'))
RABBITMQ_HEATBEAT = os.environ.get('RABBITMQ_HEATBEAT', 600)
RABBITMQ_BLOCKED_CONNECTION_TIMEOUT = os.environ.get('RABBITMQ_BLOCKED_CONNECTION_TIMEOUT', 300)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
                    )

logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/buybook')
def index():
    return render_template('index.html')

# @app.route('/csstest')
# def csstest():
#     return render_template('csstest.html')


class Callback():
    def __init__(self, corr_id):
        self.corr_id = corr_id
        self.response: Union[AnyStr, None] = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            logger.info(f" [5] Callback({self.corr_id}) is received")
            self.response = str(body, "utf-8")


@app.route('/buybook/<keyword>')
def send(keyword: str):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials,
                                  heartbeat=RABBITMQ_HEATBEAT,
                                  blocked_connection_timeout=RABBITMQ_BLOCKED_CONNECTION_TIMEOUT))
    corr_id = str(uuid.uuid4())
    cb = Callback(corr_id)
    channel = connection.channel()

    # declare exlusive callback queue for each search
    result = channel.queue_declare('', exclusive=True)
    callback_queue = result.method.queue
    channel.basic_consume(
        queue=callback_queue,
        on_message_callback=cb.on_response,
        auto_ack=True)

    # declare shared search queue
    logger.info(f" [1] Sending keyword {keyword} to Search queue w/ Callback({corr_id})")
    channel.basic_publish(
        exchange='',
        routing_key=RABBITMQ_ROUTINGKEY,
        properties=pika.BasicProperties(
            reply_to=callback_queue,
            correlation_id=corr_id,
        ),
        body=bytes(keyword, "utf-8"))

    logger.info(f" [2] Waiting for Callback({corr_id})")
    while cb.response is None:
        connection.process_data_events()

    logger.info(f" [6] Receive {cb.response}")
    return render_template(
        "buybook.html",
        table= json.loads(cb.response))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')