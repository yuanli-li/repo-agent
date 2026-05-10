SECRET_TOKEN = "secret123"


def verify_token(token: str) -> bool:
    if not token:
        return False
    return token == SECRET_TOKEN
