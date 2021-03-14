import logging
import threading

import boto3
import prometheus_client

logger = logging.getLogger("sns-email")

_counter_errors = prometheus_client.Counter('sns_email_errors_total', 'Errors total', ['source'])

_local = threading.local()


def boto_session():
    try:
        return _local.session
    except AttributeError:
        _local.session = boto3.session.Session()
        return _local.session
