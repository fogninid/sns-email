import functools
import threading


class Counter:
    def __init__(self, initial=0):
        self._lock = threading.Lock()
        self._value = initial

    def inc(self, amount=1):
        with self._lock:
            self._value += amount
            return self._value

    @property
    def value(self):
        with self._lock:
            return self._value


@functools.lru_cache
def _counter(m_id):
    return Counter()


def count(message_id):
    return _counter(message_id).inc()
