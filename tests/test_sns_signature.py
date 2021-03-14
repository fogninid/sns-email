import json

import pytest

from sns_email.sns_signature import sns_verify_signature, InvalidSnsSignatureException


@pytest.fixture(scope="session")
def valid_body(test_data_dir) -> dict:
    with open(test_data_dir / "sns-notification", "rb") as f:
        return json.load(f)


def test_sns_verify_signature(valid_body):
    sns_verify_signature(valid_body)


def test_sns_verify_signature_unknown_signature_version(valid_body):
    body = valid_body.copy()
    body["SignatureVersion"] = "2"
    with pytest.raises(Exception, match="Signature version not implemented. version=2"):
        sns_verify_signature(body)


def test_sns_verify_signature_invalid_signature(valid_body):
    body = valid_body.copy()
    body["Signature"] = "dGVzdAo="
    with pytest.raises(InvalidSnsSignatureException, match="Invalid signature"):
        sns_verify_signature(body)


def test_sns_verify_signature_bad_key_type(valid_body):
    body = valid_body.copy()
    body["Subject"] = 1
    with pytest.raises(InvalidSnsSignatureException, match="Missing key. name=Subject"):
        sns_verify_signature(body)


def test_sns_verify_signature_missing_key(valid_body):
    body = valid_body.copy()
    del body["Message"]
    with pytest.raises(InvalidSnsSignatureException, match="Missing key. name=Message"):
        sns_verify_signature(body)


def test_sns_verify_signature_missing_signature(valid_body):
    body = valid_body.copy()
    del body["Signature"]
    with pytest.raises(InvalidSnsSignatureException, match="Missing key. name=Signature"):
        sns_verify_signature(body)


def test_sns_verify_signature_invalid_signature_encoding(valid_body):
    body = valid_body.copy()
    body["Signature"] = "=notBase64"
    with pytest.raises(InvalidSnsSignatureException, match="Invalid signature"):
        sns_verify_signature(body)


def test_sns_verify_signature_untrusted_signing_url(valid_body):
    body = valid_body.copy()
    body["SigningCertURL"] = "http://example.com/badcaffe"
    with pytest.raises(InvalidSnsSignatureException, match=r"Invalid signing cert url.*"):
        sns_verify_signature(body)
