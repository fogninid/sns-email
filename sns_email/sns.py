#!/usr/bin/env python
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple

import prometheus_client

from sns_email import logger, _counter_errors
from sns_email.receive import MessageReceiver
from sns_email.sns_signature import sns_verify_signature, InvalidSnsSignatureException

_logger = logger.getChild('sns')

_counter_sns = prometheus_client.Counter('sns_email_sns_received_total', 'SNS received total')


class SnsHandler(BaseHTTPRequestHandler):
    receiver: MessageReceiver = None

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        try:
            content_bytes = self.rfile.read(content_length)
            _logger.debug("processing message. headers=%s, content=%s", self.headers, content_bytes)
            try:
                body = json.loads(content_bytes)
                sns_verify_signature(body)
            except json.decoder.JSONDecodeError:
                _logger.warning("ignoring invalid message. content=%s", content_bytes, exc_info=True)
                _counter_errors.labels('sns').inc()
            except InvalidSnsSignatureException:
                _logger.warning("ignoring message with invalid signature. content=%s", content_bytes, exc_info=True)
                _counter_errors.labels('sns').inc()
            else:
                if self.receiver is not None:
                    self.receiver.receive(body)
                else:
                    _logger.info("received notification. body=%s", body)
                _counter_sns.inc()

            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Length', '0')
            self.end_headers()
        except:
            _logger.warning("unexpected error.", exc_info=True)
            _counter_errors.labels('sns').inc()
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.send_header('Content-Length', '0')
            self.end_headers()

    def log_message(self, fmt, *args):
        _logger.debug(fmt % args)

    @classmethod
    def factory(cls, receiver: MessageReceiver, extra_bases=()):
        """Returns a dynamic SnsHandler class tied to the passed receiver. """
        cls_name = str(cls.__name__)
        return type(cls_name, (cls,) + extra_bases + (object,), {"receiver": receiver})


class SnsServer(HTTPServer):
    def __init__(self, receiver: MessageReceiver, server_address: Tuple[str, int]):
        sns_handler = SnsHandler.factory(receiver=receiver, extra_bases=(prometheus_client.MetricsHandler,))
        super().__init__(server_address, sns_handler)

    def handle_error(self, request: bytes, client_address: Tuple[str, int]) -> None:
        _logger.debug("unhandled error", exc_info=True)
