from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel, HttpUrl

import pika
import json

app = FastAPI()

rabbitmq_connection = None
rabbitmq_channel = None
queue_name = "url_scan_queue"


class ScanURLRequest(BaseModel):
    url: HttpUrl


def create_rabbitmq_connection():
    connection_params = pika.ConnectionParameters("localhost")
    return pika.BlockingConnection(connection_params)


def send_message_to_queue(url: str, timestamp: str = None):
    global rabbitmq_channel, queue_name
    message = json.dumps(
        {"url": url, "timestamp": timestamp or datetime.now().isoformat()}
    )
    rabbitmq_channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,
        ),
    )
    print(f"Sent URL to queue: {url}")


async def startup_event():
    global rabbitmq_connection, rabbitmq_channel, queue_name
    rabbitmq_connection = create_rabbitmq_connection()
    rabbitmq_channel = rabbitmq_connection.channel()
    rabbitmq_channel.queue_declare(queue=queue_name, durable=True)


async def shutdown_event():
    global rabbitmq_connection
    if rabbitmq_connection:
        rabbitmq_connection.close()


app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)


@app.post("/scan_url", status_code=202)
async def scan_url(request: ScanURLRequest):
    url = str(request.url, datetime.now().isoformat())
    send_message_to_queue(url)
    return {"message": "URL accepted and being processed.", "url": url}
