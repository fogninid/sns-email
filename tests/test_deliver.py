def test_sendmail_deliver(mock_sendmail_deliver):
    with mock_sendmail_deliver("a@example.com", []) as a:
        a.write("test".encode("utf-8"))
    for f in mock_sendmail_deliver.out_path.iterdir():
        print(f)
