import json
import logging
import pika
import traceback

from time import sleep
from functools import partial

class RabbitMQ:
    def __init__(self, host, port, user, password, logger):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.logger = logger

    def __get_pika_connection(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(self.host, self.port, "/", credentials=credentials)
        return pika.BlockingConnection(parameters)

    def send_json_message(self, queue, message):
        message = json.dumps(message)
        connection = self.__get_pika_connection()
        channel = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_publish(exchange='', routing_key=queue, body=message)

    def __on_message_callback(self, ch, method, properties, body, processing_function):
        self.logger.info(" [x] Received %r" % body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        message= json.loads(body)
        jobId = message["jobId"]
        processing_function(jobId, message["payload"])

    def listen_to_messages(self, queue_name, processing_function):
        while True:
            try:
                connection = self.__get_pika_connection()
                channel = connection.channel()

                channel.queue_declare(queue=queue_name, durable=True)
                channel.basic_consume(queue=queue_name, on_message_callback=partial(self.__on_message_callback, processing_function=processing_function))
                self.logger.info(' [*] Waiting for messages. To exit press CTRL+C')
                channel.start_consuming()
            except Exception:
                self.logger.error(traceback.format_exc())
                sleep(20)