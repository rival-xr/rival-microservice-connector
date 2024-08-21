import json
import pika
import traceback
import logging

from time import sleep
from functools import partial

import pika.exceptions

STATUS_QUEUE_NAME = "job_status"

class RabbitMQ:
    def __init__(self, host, port, user, password, max_priority = None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.logger = logging.getLogger(__name__)
        self.max_priority = max_priority
        logging.getLogger("pika").setLevel(logging.WARN)

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
        jobId = message["jobId"]
        self.send_json_message(STATUS_QUEUE_NAME, {"jobId": jobId, "status": "IN_PROGRESS"})
        ch.basic_ack(delivery_tag=method.delivery_tag)
        message= json.loads(body)
        processing_function(jobId, message["payload"])

    def listen_to_messages(self, queue_name, processing_function):
        while True:
            try:
                connection = self.__get_pika_connection()
                channel = connection.channel()
                channel.basic_qos(prefetch_count=1, global_qos=True)
                arg = {}
                if self.max_priority:
                    arg = {"x-max-priority": self.max_priority}
                try:
                    channel.queue_declare(queue=queue_name, durable=True, arguments=arg)
                except pika.exceptions.AMQPChannelError as e:
                    if e.args[0] == 406 and "PRECONDITION_FAILED" in e.args[1] and "x-max-priority" in e.args[1]:
                        channel.queue_delete(queue=queue_name)
                        channel.queue_declare(queue=queue_name, durable=True, arguments=arg)
                channel.basic_consume(queue=queue_name, on_message_callback=partial(self.__on_message_callback, processing_function=processing_function))
                self.logger.info(' [*] Waiting for messages. To exit press CTRL+C')
                channel.start_consuming()
            except Exception:
                self.logger.error(traceback.format_exc())
                sleep(20)
