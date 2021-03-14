#!/usr/bin/env python
import json
import threading
import time

import prometheus_client

from sns_email import boto_session, _counter_errors, logger
from sns_email.receive import MessageReceiver

_logger = logger.getChild('sqs')

_counter_sqs_poll = prometheus_client.Counter('sns_email_sqs_poll_total', 'SQS poll total')
_counter_sqs = prometheus_client.Counter('sns_email_sqs_received_total', 'SQS received total')


class SqsPoller:
    def __init__(self, receiver: MessageReceiver, queue_url: str, region: str):
        self.receiver = receiver
        self.queue_url = queue_url
        self.region = region

        self.poll_wait_empty = 10 * 60
        self.poll_wait = 10

        self._close = threading.Event()

    def close(self):
        _logger.info("closing.")
        self._close.set()

    def run(self):
        try:
            self.poll_forever()
        except:
            _logger.warning("uncaught exception.", exc_info=True)
            _counter_errors.labels('sqs').inc()

    def poll_forever(self):
        sqs = boto_session().client('sqs', region_name=self.region)
        _logger.info("begin polling.")
        while not self._close.is_set():
            try:
                response = sqs.receive_message(QueueUrl=self.queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=10)
                _counter_sqs_poll.inc()
                if 'Messages' in response:
                    messages = response['Messages']
                    _logger.debug("processing sqs messages. messages=%s", messages)
                    for message in messages:
                        try:
                            body = json.loads(message['Body'])
                        except (json.decoder.JSONDecodeError, KeyError):
                            _logger.warning("deleting invalid message. message=%s", message, exc_info=True)
                            _counter_errors.labels('sqs').inc()
                        else:
                            self.receiver.receive(body)
                            _logger.info("processed sqs message. message_id=%s", message['MessageId'])
                            _counter_sqs.inc()
                        sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=message['ReceiptHandle'])
                    if messages:
                        self._sleep(self.poll_wait)
                        continue
            except KeyboardInterrupt:
                self.close()
                break
            except:
                _logger.warning("uncaught exception.", exc_info=True)
                _counter_errors.labels('sqs').inc()
            try:
                self._sleep(self.poll_wait_empty)
            except KeyboardInterrupt:
                self.close()
                break
        _logger.info("closed.")

    def _sleep(self, seconds: int):
        for i in range(seconds):
            if self._close.is_set():
                break
            time.sleep(1)

    def __enter__(self):
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()
