#!/usr/bin/env python
import base64
import binascii
import functools
import re

import requests
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.x509 import Certificate

from sns_email import logger

_logger = logger.getChild("sns.signature")

_valid_sns_url = re.compile(r"^https://sns\.[-a-z0-9]+\.amazonaws\.com/")


class InvalidSnsSignatureException(Exception):
    pass


@functools.lru_cache(maxsize=5)
def _load_certificate(url) -> Certificate:
    with requests.get(url, timeout=30) as r:
        r.raise_for_status()
        return x509.load_pem_x509_certificate(r.content)


def sns_verify_signature(body):
    for name in ('Type', 'Signature', 'SigningCertURL', 'SignatureVersion'):
        if name not in body:
            raise InvalidSnsSignatureException("Missing key. name=%s" % name)

    if body['SignatureVersion'] != "1":
        raise Exception("Signature version not implemented. version=%s" % body["SignatureVersion"])

    signing_cert_url = body['SigningCertURL']
    if not _valid_sns_url.match(signing_cert_url):
        raise InvalidSnsSignatureException(
            "Invalid signing cert url. url=%s, rex=%s" % (signing_cert_url, _valid_sns_url))

    sns_type = body["Type"]
    try:
        signature = base64.b64decode(body["Signature"])
    except binascii.Error as e:
        raise InvalidSnsSignatureException("Invalid signature", e)

    if sns_type == "Notification":
        if 'Subject' in body:
            names = ('Message', 'MessageId', 'Subject', 'Timestamp', 'TopicArn', 'Type')
        else:
            names = ('Message', 'MessageId', 'Timestamp', 'TopicArn', 'Type')
    else:
        names = ('Message', 'MessageId', 'SubscribeURL', 'Timestamp', 'Token', 'TopicArn', 'Type',)

    data = bytearray()
    for name in names:
        data.extend(name.encode())
        data.extend("\n".encode())
        try:
            data.extend(body[name].encode())
        except (KeyError, AttributeError):
            raise InvalidSnsSignatureException("Missing key. name=%s" % name)
        data.extend("\n".encode())

    public_key = _load_certificate(signing_cert_url).public_key()
    try:
        public_key.verify(signature=signature, data=data, algorithm=SHA1(), padding=PKCS1v15())
    except InvalidSignature as e:
        raise InvalidSnsSignatureException("Invalid signature", e)
