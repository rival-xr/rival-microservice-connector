import json
import threading
import pika
import traceback
import logging
import ssl

from time import sleep
from functools import partial
from urllib.parse import urlparse

import pika.exceptions

STATUS_QUEUE_NAME = "job_status"

class RabbitMQ:
    def __init__(self, endpoint, user, password, heartbeat_timeout=600, max_priority = None, consumer_timeout = 1800000):
        self.endpoint = endpoint
        self.user = user
        self.password = password
        self.heartbeat_timeout = heartbeat_timeout
        self.logger = logging.getLogger(__name__)
        self.max_priority = max_priority
        self.consumer_timeout = consumer_timeout
        logging.getLogger("pika").setLevel(logging.WARN)
        self.connection = None

    def __get_pika_connection(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        parsed_endpoint = urlparse(self.endpoint)
        scheme = parsed_endpoint.scheme
        if scheme == "amqps":
            ssl_options = pika.SSLOptions(ssl.create_default_context())
        elif scheme == "amqp":
            ssl_options = None
        else:
            raise ValueError(f"Invalid scheme {scheme} in endpoint {self.endpoint}")
        parameters = pika.ConnectionParameters(parsed_endpoint.hostname, parsed_endpoint.port, "/", credentials=credentials, ssl_options=ssl_options, heartbeat=self.heartbeat_timeout)
        return pika.BlockingConnection(parameters)
    
    def close_connection(self):
        if self.connection is not None:
            self.connection.close()

    def send_json_message(self, queue, message):
        message = json.dumps(message)
        connection = self.__get_pika_connection()
        channel = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_publish(exchange='', routing_key=queue, body=message)
        channel.close()
        connection.close()

    def __on_message_callback(self, ch, method, properties, body, processing_function, queue_name):
        message= json.loads(body)
        self.logger.info(" [x] Received message on queue %s: %r", queue_name, body)
        jobId = message["jobId"]
        self.send_json_message(STATUS_QUEUE_NAME, {"jobId": jobId, "status": "IN_PROGRESS"})
        return processing_function(jobId, message["payload"], ch, method)

    def nack_message(self, ch, method, requeue: bool = False):
        if ch.is_open:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=requeue)
        else:
            self.logger.error("Channel is closed, cannot nack message")
            pass

    def ack_message(self, ch, method):
        if ch.is_open:
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            self.logger.error("Channel is closed, cannot ack message")
            pass

    def threadsafe_nack_message(self, ch, method, requeue: bool = False):
        nack_cb = partial(self.nack_message, ch=ch, method=method, requeue=requeue)
        self.connection.add_callback_threadsafe(nack_cb)

    def threadsafe_ack_message(self, ch, method):
        ack_cb = partial(self.ack_message, ch=ch, method=method)
        self.connection.add_callback_threadsafe(ack_cb)

    def create_channel(self):
        if self.connection is None or self.connection.is_closed:
            self.connection = self.__get_pika_connection()
        channel = self.connection.channel()
        channel.basic_qos(prefetch_count=1, global_qos=True)
        return channel
    
    def declare_queue(self, channel, queue_name):
        arg = {}
        if self.max_priority:
            arg["x-max-priority"] = self.max_priority
        if self.consumer_timeout:
            arg["x-consumer-timeout"] = self.consumer_timeout
        try:
            self.logger.info(f"Declaring RabbitMq queue {queue_name} with arguments {arg}")
            channel.queue_declare(queue=queue_name, durable=True, arguments=arg)
        except pika.exceptions.AMQPChannelError as e:
            if e.args[0] == 406 and "PRECONDITION_FAILED" in e.args[1] and "x-max-priority" in e.args[1]:
                channel.queue_delete(queue=queue_name)
                channel.queue_declare(queue=queue_name, durable=True, arguments=arg)

    def listen_to_messages(self, queue_name, processing_function):
        while True:
            try:
                channel = self.create_channel()
                self.declare_queue(channel, queue_name)
                channel.basic_consume(queue=queue_name, on_message_callback=partial(self.__on_message_callback, processing_function=processing_function, queue_name=queue_name))
                self.logger.info(' [*] Waiting for messages. To exit press CTRL+C')
                channel.start_consuming()
                self.logger.info("start_consuming call exited")
            except Exception:
                self.logger.error(traceback.format_exc())
                if channel is not None:
                    channel.stop_consuming()
                    channel.close()
                self.close_connection()
                sleep(20)

    def run_heartbeat(self, connection, stop_event):
        """Heartbeat function to keep RabbitMQ connection alive. This is not needed if consuming events in a loop."""
        try:
            # Send heartbeat every 60 seconds
            while not stop_event.wait(60):
                connection.process_data_events()
                self.logger.info("Heartbeat sent.")
        except Exception as e:
            self.logger.error(f"Heartbeat failed: {e}")

    def process_one_message(self, queue_name, processing_function):
        channel = self.create_channel()
        self.declare_queue(channel, queue_name)
        method_frame, header_frame, body = channel.basic_get(queue=queue_name)
        return_value = 0
        if method_frame:
            stop_event = threading.Event()
            heartbeat_thread = threading.Thread(target=self.run_heartbeat, args=(self.connection, stop_event), daemon=True)
            heartbeat_thread.start()
            try:
                return_value = self.__on_message_callback(channel, method_frame, None, body, processing_function, queue_name)
            finally:
                stop_event.set()
                heartbeat_thread.join()
        else:
            self.logger.info("No message found in queue %s", queue_name)
        channel.close()
        return return_value