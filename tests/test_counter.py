from sns_email.counter import count


class TestCounter:
    def test_count(self):
        assert count(2) == 1
        assert count(2) == 2
        assert count(3) == 1
        assert count(2) == 3

    def test_count_2(self):
        assert count(2) == 1
