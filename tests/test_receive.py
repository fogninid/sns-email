import json

from sns_email.receive import MessageReceiver


def mock_boto_session():
    return ""


def test_mail_receive(mock_deliver, test_data_dir):
    receiver = MessageReceiver(deliver=mock_deliver, boto_session=mock_boto_session)
    with open(test_data_dir / "sns-notification", "rb") as f:
        receiver.receive(json.load(f))

    assert mock_deliver.delivered
    with open(test_data_dir / "email", "rb") as f:
        assert mock_deliver.delivered[0] == f.read().decode("utf-8")
