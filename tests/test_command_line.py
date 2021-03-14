import logging
import os
import re
from unittest import mock

import pytest

from sns_email import command_line


@pytest.fixture(autouse=True)
def mock_sqs():
    with mock.patch('sns_email.command_line.SqsPoller', spec=True) as m:
        yield m


@pytest.fixture(autouse=True)
def mock_sns():
    with mock.patch('sns_email.command_line.SnsServer', spec=True) as m:
        m.__call__().server_address = ("localhost", 10000)
        yield m


@pytest.fixture(autouse=True)
def mock_logging():
    with mock.patch('sns_email.command_line.logging') as m:
        m.DEBUG = logging.DEBUG
        m.INFO = logging.INFO
        yield m


@pytest.fixture(autouse=True)
def mock_message_receiver():
    with mock.patch('sns_email.command_line.MessageReceiver') as m:
        yield m


def test_defaults(mock_sqs, mock_sns, mock_logging, mock_message_receiver):
    command_line.main([])

    mock_logging.basicConfig.assert_called_with(level=logging.INFO, format=mock.ANY, datefmt=mock.ANY)
    mock_sns.assert_called_with(receiver=mock.ANY, server_address=("localhost", 10000))
    mock_sqs.assert_not_called()
    mock_message_receiver.assert_called_with(rex=re.compile(r".*"))


def test_destination_from_env(mock_logging, mock_message_receiver):
    with mock.patch.dict(os.environ, {"SNS_EMAIL_ACCEPT_DESTINATION": "[ab]+@test\\.com"}):
        command_line.main([])
    mock_message_receiver.assert_called_with(rex=re.compile(r"[ab]+@test\.com"))


def test_destination_from_config(tmp_path, mock_logging, mock_message_receiver):
    config_file = str(tmp_path / "config")
    with open(config_file, "wt") as f:
        f.write("accept-destination=[ac]+@test\\.com")
    command_line.main(["-c", config_file])
    mock_message_receiver.assert_called_with(rex=re.compile(r"[ac]+@test\.com"))


def test_sqs_url(mock_sqs, mock_sns, mock_logging):
    command_line.main(["--sqs-queue-url=test", "--sqs-region=eu-west-1"])

    mock_logging.basicConfig.assert_called_with(level=logging.INFO, format=mock.ANY, datefmt=mock.ANY)
    mock_sns.assert_called_with(receiver=mock.ANY, server_address=("localhost", 10000))
    mock_sqs.assert_called_with(receiver=mock.ANY, queue_url="test", region="eu-west-1")


def test_custom_address(mock_sqs, mock_sns, mock_logging):
    command_line.main(["--address=dns.name", "--port=1000"])

    mock_logging.basicConfig.assert_called_with(level=logging.INFO, format=mock.ANY, datefmt=mock.ANY)
    mock_sns.assert_called_with(receiver=mock.ANY, server_address=("dns.name", 1000))


def test_one_verbose(mock_logging):
    command_line.main(["--verbose"])

    mock_logging.basicConfig.assert_called_with(level=logging.INFO, format=mock.ANY, datefmt=mock.ANY)
    mock_logging.getLogger('sns-email').setLevel.assert_called_with(logging.DEBUG)
    mock_logging.root.setLevel.assert_not_called()


def test_two_verbose(mock_logging):
    command_line.main(["-vv"])

    mock_logging.basicConfig.assert_called_with(level=logging.INFO, format=mock.ANY, datefmt=mock.ANY)
    mock_logging.root.setLevel.assert_called_with(logging.DEBUG)
