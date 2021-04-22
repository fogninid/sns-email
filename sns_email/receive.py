#!/usr/bin/env python
import json
import re

import prometheus_client

import sns_email.deliver
from sns_email import logger, _counter_errors
from sns_email.counter import count

_receive_time = prometheus_client.Histogram('sns_email_receive_seconds', 'Time spent processing receive')

_logger = logger.getChild('receive')


class MessageReceiver:
    def __init__(self, rex=re.compile(".*"), deliver=sns_email.deliver.sendmail_deliver,
                 boto_session=sns_email.boto_session):
        self.deliver = deliver
        self.boto_session = boto_session
        self.rex = rex

    @_receive_time.time()
    def receive_mail(self, message):
        mail = message['mail']

        message_id = mail['messageId']
        with count(message_id) as dup_check:
            if dup_check:
                _logger.info("ignoring duplicate message that was fully processed. message_id=%s", message_id)
                return

            dup_count = dup_check.value
            if dup_count > 2:
                _logger.warning(
                    "aborting receiving a duplicate message that already failed. message_id=%s, dup_count=%s",
                    message_id, dup_count)
                _counter_errors.labels('receive_duplicate').inc()
                raise Exception("duplicate message")
            elif dup_count > 1:
                _logger.warning("receiving duplicate message. message_id=%s", message_id)
                _counter_errors.labels('receive_duplicate').inc()

            receipt = message['receipt']
            recipients = [d for d in receipt['recipients'] if self.rex.match(d)]
            source = mail['source']
            if not recipients:
                _logger.info("ignoring mail with no local recipient. message=%s", message)
                _counter_errors.labels('receive').inc()
                return
            mail_from = source
            if 'commonHeaders' in mail and 'from' in mail['commonHeaders']:
                mail_from = mail['commonHeaders']['from']

            if 'content' in message:
                with self.deliver(source, recipients) as f:
                    f.write(message['content'])
            elif 'action' in receipt and 'type' in receipt['action']:
                if 'S3' == receipt['action']['type']:
                    with self.deliver(source, recipients) as f:
                        self.boto_session().client('s3').download_fileobj(receipt['action']['bucketName'],
                                                                          receipt['action']['objectKey'], f)
                else:
                    _logger.info("ignoring unknown receipt type. message=%s", message)
                    _counter_errors.labels('receive').inc()
            else:
                _logger.info("ignoring unknown receipt. message=%s", message)
                _counter_errors.labels('receive').inc()

            _logger.info("received email. source=%s, mail_from=%s, recipients=%s, message_id=%s",
                         source, mail_from, recipients, message_id)

    def receive(self, body: dict):
        if body['Type'] == 'Notification':
            try:
                message = json.loads(body['Message'])
            except (json.decoder.JSONDecodeError, KeyError):
                _logger.info("ignoring invalid notification. content=%s", body, exc_info=True)
                _counter_errors.labels('receive').inc()
            else:
                if 'mail' in message:
                    self.receive_mail(message)
                else:
                    _logger.info("ignoring unexpected message. message=%s", message)
                    _counter_errors.labels('receive').inc()
        else:
            _logger.info("ignoring unexpected message. body=%s", body)
            _counter_errors.labels('receive').inc()
