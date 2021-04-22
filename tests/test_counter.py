from sns_email.counter import count


class TestCounter:
    def test_count(self):
        with count(2) as c:
            assert c.value == 1
            assert not c
            with count(2) as c2:
                assert c2.value == 2
                assert not c2
            assert c

        with count(3) as c:
            assert c.value == 1
        with count(2) as c:
            assert c

    def test_count_failure(self):
        try:
            with count(2) as c:
                assert c.value == 1
                assert not c
                raise ValueError()
        except ValueError:
            pass

        with count(2) as c:
            assert not c
            assert c.value == 2
        with count(2) as c:
            assert c

    def test_count_independent(self):
        with count(1) as c1, count(2) as c2:
            assert c1 is not c2
            assert c1.value == 1
            assert c2.value == 1

        with count(1) as c1, count(2) as c2:
            assert c1 is not c2
            assert c1
            assert c2
