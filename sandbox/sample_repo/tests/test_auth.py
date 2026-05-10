from auth import verify_token


def test_verify_token_success():
    assert verify_token("secret123") is True


def test_verify_token_fail():
    assert verify_token("wrong-token") is False


def test_verify_token_empty():
    assert verify_token("") is False
