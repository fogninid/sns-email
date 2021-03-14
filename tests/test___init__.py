from concurrent.futures.thread import ThreadPoolExecutor

from sns_email import boto_session


def test_boto_session():
    def get_it():
        return boto_session()

    assert get_it() is get_it()

    count = 5
    r = set()
    r.add(get_it())

    with ThreadPoolExecutor(max_workers=count) as executor:
        futures = []
        for i in range(count):
            futures.append(executor.submit(get_it))

        for f in futures:
            r.add(f.result())

        assert executor.submit(lambda: get_it() is get_it()).result()

    assert 2 <= len(r) <= count + 1
