import functools
import threading


class Counter:
    def __init__(self, initial=0):
        self._lock = threading.Lock()
        self._value = initial
        self._success = False

    def __bool__(self):
        with self._lock:
            return self._success

    def inc(self, amount=1):
        with self._lock:
            self._value += amount
            return self._value

    def set_success(self):
        with self._lock:
            self._success = True
            self._value = 0

    @property
    def value(self):
        with self._lock:
            return self._value

    def __enter__(self):
        self.inc()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is None:
            self.set_success()


@functools.lru_cache
def _counter(m_id):
    return Counter()


def count(message_id) -> Counter:
    return _counter(message_id)
