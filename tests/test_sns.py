import threading
from unittest import mock

import prometheus_client
import prometheus_client.parser
import pytest
import requests

import sns_email
from sns_email.receive import MessageReceiver
from sns_email.sns import SnsServer

_logger = sns_email.logger.getChild("test")


class test_server:
    def __init__(self, receiver, address):
        self._receiver = receiver
        self._server = SnsServer(self, address)

    def receive(self, body):
        try:
            self._receiver.receive(body)
        except AttributeError:
            self._receiver(body)

    def _run(self):
        with self._server as server:
            server.serve_forever()

    def __enter__(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.start()
        return self._server

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._server.shutdown()
        self._thread.join(timeout=10)
        if self._thread.is_alive():
            _logger.warn("test_server thread still alive. server=%s", self._server)


class FixtureTestServer:
    def __init__(self, server_address, received):
        self.received = received
        self.server_url = "http://%s:%d/" % server_address


@pytest.fixture
def capturing_test_server() -> FixtureTestServer:
    received = []
    with test_server(received.append, ("127.0.0.1", 0)) as t:
        yield FixtureTestServer(t.server_address, received)


@pytest.fixture
def mock_delivering_test_server(mock_deliver) -> FixtureTestServer:
    receiver = MessageReceiver(deliver=mock_deliver)
    with test_server(receiver, ("127.0.0.1", 0)) as t:
        yield FixtureTestServer(t.server_address, mock_deliver.delivered)


def test_metrics(capturing_test_server):
    with requests.get(capturing_test_server.server_url) as response:
        response_text = response.text
        assert response.ok, "status=%d, text=%s" % (response.status_code, response_text)

    metric_names = set([
        metric.name for metric in prometheus_client.parser.text_string_to_metric_families(response_text)
        if metric.name.startswith("sns_")
    ])

    assert {'sns_email_errors', 'sns_email_receive_seconds', 'sns_email_received', 'sns_email_sns_received'} \
        .issubset(metric_names)


def test_request(capturing_test_server, test_data_dir):
    capturing_test_server.received.clear()

    with open(test_data_dir / "sns-notification", "rb") as f:
        with requests.post(capturing_test_server.server_url, data=f) as response:
            assert response.ok, "status=%d, text=%s" % (response.status_code, response.text)

    assert len(capturing_test_server.received) == 1


def test_request_ignores_bad_signature(capturing_test_server, test_data_dir):
    capturing_test_server.received.clear()

    with mock.patch("sns_email.sns._logger") as m:
        with requests.post(capturing_test_server.server_url, json={}) as response:
            assert response.ok, "status=%d, text=%s" % (response.status_code, response.text)
        m.warning.assert_called_with("ignoring message with invalid signature. content=%s", b'{}', exc_info=True)

    assert len(capturing_test_server.received) == 0


def test_request_and_deliver(mock_delivering_test_server, test_data_dir):
    with open(test_data_dir / "sns-notification", "rb") as f:
        with requests.post(mock_delivering_test_server.server_url, data=f) as response:
            assert response.ok, "status=%d, text=%s" % (response.status_code, response.text)

    assert len(mock_delivering_test_server.received) == 1
    with open(test_data_dir / "email", "rb") as f:
        assert mock_delivering_test_server.received[0] == f.read().decode("utf-8")

    for i in range(10):
        with open(test_data_dir / "sns-notification", "rb") as f:
            with requests.post(mock_delivering_test_server.server_url, data=f) as response:
                assert response.ok, "i=%d, status=%d, text=%s" % (i, response.status_code, response.text)

    assert len(mock_delivering_test_server.received) == 1


def test_request_and_deliver_failure(mock_delivering_test_server, mock_deliver, test_data_dir):
    mock_deliver.failure = ValueError()

    with open(test_data_dir / "sns-notification", "rb") as f:
        with requests.post(mock_delivering_test_server.server_url, data=f) as response:
            assert not response.ok, "status=%d, text=%s" % (response.status_code, response.text)
