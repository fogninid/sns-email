import io
import re
from pathlib import Path
from unittest import mock

import pytest

from sns_email import counter
from sns_email.deliver import sendmail_deliver


@pytest.fixture(autouse=True)
def reset():
    counter._counter.cache_clear()


@pytest.fixture(autouse=True, scope="session")
def mock_signing(test_data_dir):
    with mock.patch("sns_email.sns_signature._valid_sns_url", new=re.compile("https://.*")), \
         mock.patch("sns_email.sns_signature.requests") as m:
        with open(test_data_dir / "signing-key.pem", "rb") as f:
            m.get().__enter__().content = f.read(4096)
        yield


@pytest.fixture
def mock_deliver():
    class mock_deliver:
        delivered = []
        failure = None

        def __init__(self, source, recipients):
            self.source = source
            self.recipients = recipients

        def __enter__(self):
            self.string_io = io.StringIO()
            return self.string_io

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.failure is not None:
                raise self.failure
            self.delivered.append(self.string_io.getvalue())

    return mock_deliver


@pytest.fixture
def mock_sendmail_deliver(tmp_path):
    path = tmp_path / "sendmail"

    with path.open("w") as f:
        f.write(f"""#!/bin/sh
cat > '{tmp_path}'/out/rec
""")
    path.chmod(0o777)

    class mock_sendmail_deliver(sendmail_deliver):
        out_path = tmp_path / "out"

        def __init__(self, source, recipients):
            super().__init__(source, recipients, sendmail_path=str(path))
            self.out_path.mkdir(parents=True, exist_ok=True)

    return mock_sendmail_deliver


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    return Path(__file__).parent / "test-data"
