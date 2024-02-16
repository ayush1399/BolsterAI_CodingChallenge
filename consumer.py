import pika
import json
import datetime

from peewee import *
from datetime import datetime
from playhouse.postgres_ext import *

from script import PlaywrightScanner

db = PostgresqlDatabase(
    "postgres",
    user="ayush1399",
    host="localhost",
    port=5432,
)

db.connect()


class URL(Model):
    url = TextField()
    received_at = DateTimeField(default=datetime.now)
    processed_at = DateTimeField(null=True)
    info = JSONField()

    class Meta:
        database = db


db.create_tables([URL])


def on_message_received(ch, method, properties, body):
    message = json.loads(body)
    url = message["url"]
    request_timestamp = message["timestamp"]
    print(f"Consumer processing URL: {url}")

    scanner = PlaywrightScanner(url)
    info = scanner.process_url()
    processed_at = datetime.now().isoformat()

    try:
        new_url = URL.create(
            url=url, info=info, processed_at=processed_at, received_at=request_timestamp
        )
    except Exception as e:
        print(f"Error saving URL: {e}")

    # Acknowledge the message
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consuming_messages():
    connection_params = pika.ConnectionParameters("localhost")
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    queue_name = "url_scan_queue"

    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=on_message_received)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()
    db.close()


if __name__ == "__main__":
    start_consuming_messages()
